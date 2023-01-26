from pathlib import Path
import sys
import os
# Adding the path to the root folder so the files can be imported in the tests
ROOT_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_PATH))

os.environ['TEST_ROOT'] = str(Path(__file__).parent.parent)
