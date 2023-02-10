from pathlib import Path
import sys
import os
# Adding the path to the root folder so the files can be imported in the tests

TESTS_ROOT = Path(os.path.dirname(__file__))
PROJECT_ROOT_PATH = TESTS_ROOT.parent
MAIN_PROJECT_FILES_PATH = PROJECT_ROOT_PATH / 'src'
# sys.path.insert(0, str(PROJECT_ROOT_PATH))
sys.path.insert(0, str(MAIN_PROJECT_FILES_PATH))

os.environ['TEST_ROOT'] = str(Path(TESTS_ROOT))
