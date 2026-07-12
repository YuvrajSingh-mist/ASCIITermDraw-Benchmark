.PHONY: generate render verify

generate:
	python3 generate_benchmark.py

render:
	python3 scripts/render_all.py

verify:
	@echo "Task categories: $$(find tasks -mindepth 1 -maxdepth 1 -type d | wc -l)"
	@echo "Task directories: $$(find tasks -mindepth 2 -maxdepth 2 -type d | wc -l)"
	@echo "prompt.txt files: $$(find tasks -name prompt.txt | wc -l)"
	@echo "reference.ascii:  $$(find tasks -name reference.ascii | wc -l)"
	@echo "assertions.json:  $$(find tasks -name assertions.json | wc -l)"
	@echo "vlm_judge_prompt: $$(find tasks -name vlm_judge_prompt.txt | wc -l)"
	@echo "source.ascii:     $$(find tasks -name source.ascii | wc -l)"
