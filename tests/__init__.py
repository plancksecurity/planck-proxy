from pathlib import Path
import sys
# Adding the path to the commons folder so it can be used as a module anywhere
ROOT_PATH = Path(__file__).parent
sys.path.insert(0, str(ROOT_PATH))
