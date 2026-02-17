/**
 * LaTeX Editor functionality with CodeMirror and PDF preview
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror
    const textarea = document.getElementById('latex-editor');
    const editor = CodeMirror.fromTextArea(textarea, {
        mode: 'stex',
        theme: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dracula' : 'eclipse',
        lineNumbers: true,
        lineWrapping: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        indentUnit: 2,
        tabSize: 2,
        extraKeys: {
            'Ctrl-Space': 'autocomplete',
            'Ctrl-S': function(cm) { compileLatex(); },
            'Cmd-S': function(cm) { compileLatex(); }
        }
    });

    // Track current PDF data
    let currentPdfBase64 = typeof initialPdfBase64 !== 'undefined' ? initialPdfBase64 : '';
    let currentPdfDoc = null;
    let currentZoom = 1.0;
    let compileTimeout = null;
    let lastCompileTime = null;

    // Elements
    const statusIndicator = document.getElementById('status-indicator');
    const cursorPosition = document.getElementById('cursor-position');
    const lastCompiled = document.getElementById('last-compiled');
    const compileBtn = document.getElementById('btn-compile');
    const exportBtn = document.getElementById('btn-export');
    const exportForm = document.getElementById('export-form');
    const exportLatexContent = document.getElementById('export-latex-content');

    // Initialize PDF if available
    if (currentPdfBase64) {
        renderPdf(currentPdfBase64);
    }

    // Debounced auto-compile
    editor.on('change', function() {
        if (compileTimeout) {
            clearTimeout(compileTimeout);
        }
        setStatus('compiling');
        compileTimeout = setTimeout(function() {
            compileLatex();
        }, 1000);
    });

    // Cursor position tracking
    editor.on('cursorActivity', function() {
        const pos = editor.getCursor();
        cursorPosition.textContent = `Line ${pos.line + 1}, Col ${pos.ch + 1}`;
    });

    // Compile button
    if (compileBtn) {
        compileBtn.addEventListener('click', function() {
            compileLatex();
        });
    }

    // Export button
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const latexContent = editor.getValue();
            exportLatexContent.value = latexContent;
            exportForm.submit();
        });
    }

    // Copy LaTeX button
    const copyLatexBtn = document.getElementById('btn-copy-latex');
    if (copyLatexBtn) {
        copyLatexBtn.addEventListener('click', function() {
            const latexContent = editor.getValue();
            navigator.clipboard.writeText(latexContent).then(function() {
                showToast('LaTeX copied to clipboard!');
            });
        });
    }

    // PDF Zoom controls
    const zoomInBtn = document.getElementById('pdf-zoom-in');
    const zoomOutBtn = document.getElementById('pdf-zoom-out');
    const zoomLevel = document.getElementById('pdf-zoom-level');

    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', function() {
            currentZoom = Math.min(currentZoom + 0.1, 2.0);
            zoomLevel.textContent = Math.round(currentZoom * 100) + '%';
            if (currentPdfDoc) {
                const pdfContainer = document.getElementById('pdf-container');
                pdfContainer.innerHTML = '';
                for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
                    renderPdfPage(pageNum, pdfContainer);
                }
            }
        });
    }

    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', function() {
            currentZoom = Math.max(currentZoom - 0.1, 0.5);
            zoomLevel.textContent = Math.round(currentZoom * 100) + '%';
            if (currentPdfDoc) {
                const pdfContainer = document.getElementById('pdf-container');
                pdfContainer.innerHTML = '';
                for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
                    renderPdfPage(pageNum, pdfContainer);
                }
            }
        });
    }

    // Split pane resize handling
    const resizeHandle = document.getElementById('resize-handle');
    const leftPane = document.querySelector('.editor-pane-left');
    const rightPane = document.querySelector('.editor-pane-right');

    let isResizing = false;

    if (resizeHandle) {
        resizeHandle.addEventListener('mousedown', function(e) {
            isResizing = true;
            resizeHandle.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', function(e) {
            if (!isResizing) return;

            const container = document.querySelector('.editor-split');
            const containerRect = container.getBoundingClientRect();
            const leftWidth = e.clientX - containerRect.left;
            const percentage = (leftWidth / containerRect.width) * 100;

            if (percentage > 20 && percentage < 80) {
                leftPane.style.flex = 'none';
                leftPane.style.width = percentage + '%';
                rightPane.style.flex = 'none';
                rightPane.style.width = (100 - percentage) + '%';
            }
        });

        document.addEventListener('mouseup', function() {
            if (isResizing) {
                isResizing = false;
                resizeHandle.classList.remove('resizing');
                document.body.style.cursor = '';
            }
        });
    }

    // Theme change handler
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                const theme = document.documentElement.getAttribute('data-theme');
                editor.setOption('theme', theme === 'dark' ? 'dracula' : 'eclipse');
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true });

    // Compile LaTeX to PDF
    function compileLatex() {
        const latexContent = editor.getValue();
        if (!latexContent.trim()) return;

        setStatus('compiling');
        const compileIcon = document.getElementById('compile-icon');
        if (compileIcon) compileIcon.style.animation = 'spin 1s linear infinite';

        fetch('/editor/compile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'latex_content=' + encodeURIComponent(latexContent)
        })
        .then(response => response.json())
        .then(data => {
            if (compileIcon) compileIcon.style.animation = '';

            if (data.success && data.pdf_base64) {
                currentPdfBase64 = data.pdf_base64;
                renderPdf(data.pdf_base64);
                setStatus('ready');
                lastCompileTime = new Date();
                updateLastCompiled();
            } else {
                setStatus('error', data.error || 'Compilation failed');
                showError(data.error || 'Failed to compile LaTeX');
            }
        })
        .catch(error => {
            if (compileIcon) compileIcon.style.animation = '';
            setStatus('error', error.message);
            showError('Network error: ' + error.message);
        });
    }

    // Render PDF using PDF.js
    function renderPdf(pdfBase64) {
        const pdfContainer = document.getElementById('pdf-container');
        if (!pdfContainer) return;

        const pdfData = atob(pdfBase64);
        const pdfArray = new Uint8Array(pdfData.length);
        for (let i = 0; i < pdfData.length; i++) {
            pdfArray[i] = pdfData.charCodeAt(i);
        }

        pdfjsLib.getDocument({ data: pdfArray }).promise.then(function(pdf) {
            currentPdfDoc = pdf;

            // Clear container and render all pages
            pdfContainer.innerHTML = '';

            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                renderPdfPage(pageNum, pdfContainer);
            }
        }).catch(function(error) {
            showError('PDF render error: ' + error.message);
        });
    }

    // Render a specific PDF page with high DPI support
    function renderPdfPage(pageNumber, container) {
        if (!currentPdfDoc) return;

        currentPdfDoc.getPage(pageNumber).then(function(page) {
            // Get device pixel ratio for high DPI (Retina/4K) support
            const pixelRatio = window.devicePixelRatio || 1;

            // Create viewport with pixel ratio scaling
            const viewport = page.getViewport({ scale: currentZoom * pixelRatio });

            // Create canvas for this page
            const pageCanvas = document.createElement('canvas');
            pageCanvas.className = 'pdf-page-canvas';
            pageCanvas.style.display = 'block';

            // Set actual canvas size (scaled for high DPI)
            pageCanvas.width = viewport.width;
            pageCanvas.height = viewport.height;

            // Set display size (CSS pixels)
            pageCanvas.style.width = (viewport.width / pixelRatio) + 'px';
            pageCanvas.style.height = (viewport.height / pixelRatio) + 'px';

            // Get context with disabled anti-aliasing for sharp text
            const ctx = pageCanvas.getContext('2d');
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';

            // Create viewport at normal scale for rendering
            const renderViewport = page.getViewport({ scale: currentZoom * pixelRatio });

            const renderContext = {
                canvasContext: ctx,
                viewport: renderViewport
            };

            page.render(renderContext);
            container.appendChild(pageCanvas);
        });
    }

    // Set status indicator
    function setStatus(status, message) {
        if (!statusIndicator) return;

        const dot = statusIndicator.querySelector('.status-dot');
        const label = statusIndicator.lastChild;

        dot.className = 'status-dot status-' + status;

        switch(status) {
            case 'ready':
                label.textContent = ' Ready';
                break;
            case 'compiling':
                label.textContent = ' Compiling...';
                break;
            case 'error':
                label.textContent = ' Error: ' + (message || 'Compilation failed');
                break;
        }
    }

    // Update last compiled time
    function updateLastCompiled() {
        if (!lastCompiled || !lastCompileTime) return;

        const now = new Date();
        const diff = Math.floor((now - lastCompileTime) / 1000);

        if (diff < 60) {
            lastCompiled.textContent = 'Last compiled: ' + diff + 's ago';
        } else if (diff < 3600) {
            lastCompiled.textContent = 'Last compiled: ' + Math.floor(diff / 60) + 'm ago';
        } else {
            lastCompiled.textContent = 'Last compiled: ' + Math.floor(diff / 3600) + 'h ago';
        }
    }

    // Show error message
    function showError(message) {
        console.error(message);
        // Could add a toast notification here
    }

    // Show toast notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            background: var(--color-primary);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(toast);

        setTimeout(function() {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(function() {
                toast.remove();
            }, 300);
        }, 3000);
    }

    // Update last compiled every 10 seconds
    setInterval(updateLastCompiled, 10000);
});
