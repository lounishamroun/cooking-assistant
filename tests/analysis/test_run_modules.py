"""Coverage tests for __main__ blocks in scoring and seasonal modules."""
import runpy


def test_run_seasonal_module_main():
    # Executes the __main__ block of seasonal to cover example prints
    runpy.run_module('cooking_assistant.analysis.seasonal', run_name='__main__')


def test_run_scoring_module_main():
    # Executes the __main__ block of scoring
    runpy.run_module('cooking_assistant.analysis.scoring', run_name='__main__')
