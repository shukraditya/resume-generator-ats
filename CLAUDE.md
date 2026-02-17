# Resume Converter + ATS Analyzer

|docs=pipe-compressed-index,no-spaces

[PROJECT]|name=resume-toolchain|purpose=convert-md-to-latex-pdf+ats-analysis
|stack=Python+uv,FastAPI,Jinja2,pdflatex,KimiAPI
|output=streaming-pdf,no-disk-persistence

[ARCHITECTURE]|layer1=parser|md->structured-data
|layer2=generator|structured-data->latex->pdf-bytes->stream
|layer3=analyzer|kimi-api->ats-scores+insights|cached-1hr-ttl
|layer4=web|fastapi+jinja2->ui
|layer5=cache|in-memory|key=sha256-normalized-text|pdf=forever|ats=1hr

[FILES]|entry=main.py|source=src/|tests=tests/
|parser=md_parser.py|dataclasses=ContactInfo,Education,Experience,Project,Resume
|latex=latex_generator.py|template=embedded-preamble+charter-font
|pdf=pdf_generator.py|method=tempfile.TemporaryDirectory+pdflatex-2pass
|ats=ats_analyzer.py|provider=kimi|endpoint=/chat/completions|model=kimi-latest
|cache=cache.py|store=_cache:dict|key=sha256[:16]|ats_ttl=3600s

[MD-SCHEMA]|heading=name+contact(line1,line2)|contact-format=city,country|links|phone|email|github
|sections=education,experience,projects,skills,interests
|education=school|location|degree|date|optional(gpa,awards)
|experience=company|location|role|date|bullets
|projects=name|link|bullets
|skills=categories-with-pipes
|parsing=regex-based|bold=**|italic=*|links=[text](url)

[LATEX-TEMPLATE]|base=format.tex|commands=resumeSubheading,resumeItem,resumeProjectHeading
|fonts=charter|ats-safe=\pdfgentounicode=1|margins=adjusted(-0.5in)|pagestyle=empty

[PDF-GENERATION]|method=tempfile.TemporaryDirectory|output=bytes
|compilation=pdflatex-2pass|-interaction=nonstopmode|cleanup=auto|delivery=StreamingResponse

[ATS-AGENT]|provider=kimi|mode=standalone+job-desc-toggle
|analysis=keywords(found,missing,repeated),action-verbs(strong,weak),quantification(metrics),readability,formatting
|output=json|scores=0-100|insights=actionable-prioritized|response_format=json_object

[API-ENDPOINTS]|get=/|post=/convert|post=/convert-stream|post=/analyze
|get=/download-latex?resume_text=|get=/cache-status
|filename-pattern={base}+jake.pdf

[CACHE]|key-gen=sha256(normalized-text)[:16]|pdf-ttl=forever|ats-ttl=3600s
|status=has_pdf,has_latex,has_ats,ats_expired,age_seconds

[TESTS]|parser=test_md_parser.py|pdf=test_pdf_generator.py|cache=test_cache.py
|endpoints=test_endpoints.py|pytest-cov=available

[DEPLOY]|docker=Dockerfile|fly=fly.toml|render=render.yaml
|env=KIMI_API_KEY|port=8000

[DESIGN]|style=warm-personal-minimal|tokens=color,spacing,typography,radius
|html=semantic|css=logical-properties+minimal-utilities
