Qwen 3.5 text captures (LM Studio / OpenAI-compatible) used by @pytest.mark.manual tests.

Run only these corpora (naast de default suite zonder manual tests):
  export PYTHONPATH=backend/threat_designer
  python3 -m pytest -m manual test/threat_designer/ -v --tb=short

Default  pytest / pytest test/  sluit manual tests uit (pytest.ini: -m "not manual").

images/
  Optioneel: zet hier dezelfde architectuur-diagram(png/jpg) als bij de handmatige LLM-run.
  Huidige unit tests lezen geen binaire beelden — alleen de .md modeloutput.
  De map is bedoeld voor menselijke vergelijking of latere vision/geïntegreerde tests.
