/**
 * ATS Improvements page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get stored data
    const resumeTextInput = document.getElementById('resume-text');
    const latexContentInput = document.getElementById('latex-content');
    const resumeText = resumeTextInput ? resumeTextInput.value : '';
    const latexContent = latexContentInput ? latexContentInput.value : '';

    // State
    let suggestions = [];
    let currentLatex = latexContent;
    let appliedSuggestions = new Set();
    let rejectedSuggestions = new Set();

    // Elements
    const loadingState = document.getElementById('loading-state');
    const resultsState = document.getElementById('results-state');
    const errorState = document.getElementById('error-state');
    const errorMessage = document.getElementById('error-message');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const noSuggestions = document.getElementById('no-suggestions');
    const currentScore = document.getElementById('current-score');
    const targetScore = document.getElementById('target-score');

    // Buttons
    const btnApplyAll = document.getElementById('btn-apply-all');
    const btnRejectAll = document.getElementById('btn-reject-all');
    const btnOpenEditor = document.getElementById('btn-open-editor');

    // Generate improvements on page load
    generateImprovements();

    // Event listeners
    if (btnApplyAll) {
        btnApplyAll.addEventListener('click', applyAllSuggestions);
    }

    if (btnRejectAll) {
        btnRejectAll.addEventListener('click', rejectAllSuggestions);
    }

    if (btnOpenEditor) {
        btnOpenEditor.addEventListener('click', function(e) {
            e.preventDefault();
            openInEditor();
        });
    }

    // Generate improvement suggestions
    function generateImprovements() {
        if (!resumeText || !latexContent) {
            showError('Missing resume text or LaTeX content');
            return;
        }

        const formData = new FormData();
        formData.append('resume_text', resumeText);
        formData.append('latex_content', latexContent);

        fetch('/improve', {
            method: 'POST',
            body: new URLSearchParams({
                'resume_text': resumeText,
                'latex_content': latexContent
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }

            suggestions = data.suggestions || [];
            displayResults(data);
        })
        .catch(error => {
            showError('Failed to generate improvements: ' + error.message);
        });
    }

    // Display results
    function displayResults(data) {
        loadingState.style.display = 'none';
        resultsState.style.display = 'block';

        // Update scores
        if (currentScore) currentScore.textContent = data.overall_score || '--';
        if (targetScore) targetScore.textContent = data.target_score || '--';

        // Render suggestions
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            noSuggestions.style.display = 'block';
        } else {
            renderSuggestions();
        }
    }

    // Render suggestion cards
    function renderSuggestions() {
        suggestionsContainer.innerHTML = '';

        suggestions.forEach(suggestion => {
            const card = createSuggestionCard(suggestion);
            suggestionsContainer.appendChild(card);
        });
    }

    // Create a suggestion card element
    function createSuggestionCard(suggestion) {
        const template = document.getElementById('suggestion-template');
        const clone = template.content.cloneNode(true);
        const card = clone.querySelector('.suggestion-card');

        card.dataset.suggestionId = suggestion.id;

        // Priority label
        const priorityEl = card.querySelector('.suggestion-priority');
        const priorityLabels = { 1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low', 5: 'Suggestion' };
        priorityEl.textContent = priorityLabels[suggestion.priority] || 'Medium';
        priorityEl.className = 'suggestion-priority priority-' + suggestion.priority;

        // Section
        const sectionEl = card.querySelector('.suggestion-section');
        sectionEl.textContent = suggestion.target_section;

        // Title
        const titleEl = card.querySelector('.suggestion-title');
        titleEl.textContent = suggestion.description;

        // Reason
        const reasonEl = card.querySelector('.suggestion-reason');
        reasonEl.textContent = suggestion.reason;

        // Diff
        const diffView = card.querySelector('.diff-view code');
        diffView.innerHTML = renderDiff(suggestion.diff);

        // Buttons
        const applyBtn = card.querySelector('.btn-apply');
        const rejectBtn = card.querySelector('.btn-reject');

        applyBtn.addEventListener('click', () => applySuggestion(suggestion.id));
        rejectBtn.addEventListener('click', () => rejectSuggestion(suggestion.id));

        return card;
    }

    // Render diff with syntax highlighting
    function renderDiff(diffText) {
        if (!diffText) return '<span class="diff-empty">No diff available</span>';

        const lines = diffText.split('\n');
        let html = '';

        lines.forEach(line => {
            const escaped = escapeHtml(line);

            if (line.startsWith('---')) {
                html += `<span class="diff-line diff-file-header">${escaped}</span>\n`;
            } else if (line.startsWith('+++')) {
                html += `<span class="diff-line diff-file-header">${escaped}</span>\n`;
            } else if (line.startsWith('@@')) {
                html += `<span class="diff-line diff-hunk-header">${escaped}</span>\n`;
            } else if (line.startsWith('+')) {
                html += `<span class="diff-line diff-added">${escaped}</span>\n`;
            } else if (line.startsWith('-')) {
                html += `<span class="diff-line diff-removed">${escaped}</span>\n`;
            } else if (line.startsWith('\\')) {
                html += `<span class="diff-line">${escaped}</span>\n`;
            } else if (line.trim() === '') {
                html += `<span class="diff-line">\n</span>\n`;
            } else {
                html += `<span class="diff-line diff-context">${escaped}</span>\n`;
            }
        });

        return html;
    }

    // Escape HTML entities
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Apply a single suggestion
    function applySuggestion(suggestionId) {
        const suggestion = suggestions.find(s => s.id === suggestionId);
        if (!suggestion) return;

        fetch('/improve/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'latex_content': currentLatex,
                'diff': suggestion.diff
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentLatex = data.updated_latex;
                appliedSuggestions.add(suggestionId);

                // Update UI
                const card = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
                if (card) {
                    card.classList.add('applied');
                    const applyBtn = card.querySelector('.btn-apply');
                    if (applyBtn) {
                        applyBtn.textContent = 'Applied';
                        applyBtn.disabled = true;
                    }
                }

                showToast('Suggestion applied');
            } else {
                showError('Failed to apply suggestion: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            showError('Network error: ' + error.message);
        });
    }

    // Reject a suggestion
    function rejectSuggestion(suggestionId) {
        rejectedSuggestions.add(suggestionId);

        const card = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
        if (card) {
            card.classList.add('rejected');
            card.style.display = 'none';
        }

        // Check if all rejected
        if (rejectedSuggestions.size + appliedSuggestions.size === suggestions.length) {
            noSuggestions.style.display = 'block';
        }
    }

    // Apply all non-rejected suggestions
    function applyAllSuggestions() {
        const remainingSuggestions = suggestions.filter(s =>
            !appliedSuggestions.has(s.id) && !rejectedSuggestions.has(s.id)
        );

        if (remainingSuggestions.length === 0) {
            showToast('No suggestions to apply');
            return;
        }

        fetch('/improve/apply-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'latex_content': latexContent,  // Start from original
                'suggestions': JSON.stringify(remainingSuggestions)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentLatex = data.updated_latex;

                // Mark all as applied
                remainingSuggestions.forEach(s => {
                    appliedSuggestions.add(s.id);
                    const card = document.querySelector(`[data-suggestion-id="${s.id}"]`);
                    if (card) {
                        card.classList.add('applied');
                        const applyBtn = card.querySelector('.btn-apply');
                        if (applyBtn) {
                            applyBtn.textContent = 'Applied';
                            applyBtn.disabled = true;
                        }
                    }
                });

                showToast(`Applied ${data.applied_count} of ${data.total_count} suggestions`);
            } else {
                showError('Failed to apply suggestions: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            showError('Network error: ' + error.message);
        });
    }

    // Reject all suggestions
    function rejectAllSuggestions() {
        suggestions.forEach(s => {
            rejectedSuggestions.add(s.id);
            const card = document.querySelector(`[data-suggestion-id="${s.id}"]`);
            if (card) {
                card.style.display = 'none';
            }
        });

        noSuggestions.style.display = 'block';
        showToast('All suggestions rejected');
    }

    // Open current LaTeX in editor
    function openInEditor() {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/editor';
        form.style.display = 'none';

        const latexInput = document.createElement('textarea');
        latexInput.name = 'latex_content';
        latexInput.value = currentLatex;

        form.appendChild(latexInput);
        document.body.appendChild(form);
        form.submit();
    }

    // Show error state
    function showError(message) {
        loadingState.style.display = 'none';
        resultsState.style.display = 'none';
        errorState.style.display = 'block';
        errorMessage.textContent = message;
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
});

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
