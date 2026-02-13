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

[MD-SCHEMA]|heading=name+contact(line1,line2)|contact-format=city,country|links|phone|email|github
|sections=education,experience,projects,skills,interests
|education=school|location|degree|date|optional(gpa,awards)
|experience=company|location|role|date|bullets
|projects=name|link|bullets
|skills=categories-with-pipes

[LATEX-TEMPLATE]|base=format.tex|commands=resumeSubheading,resumeItem,etc
|fonts=charter-compatible|ats-safe=pdfgentounicode

[PDF-GENERATION]|method=tempfile.TemporaryDirectory|output=bytes
|compilation=pdflatex-2pass|cleanup=auto|delivery=StreamingResponse

[ATS-AGENT]|provider=kimi|mode=standalone+job-desc-toggle
|analysis=keywords,structure,action-verbs,quantified-achievements,readability,repetition
|output=json|scores=0-100|insights=actionable-prioritized
|cache=sha256-key|ttl=3600s

[DESIGN]|style=warm-personal-minimal|tokens=color,spacing,typography,radius
|html=semantic|css=logical-properties+minimal-utilities
