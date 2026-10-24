import ast
from pathlib import Path
import unittest
class PromptTests(unittest.TestCase):
    def test_format(self):
        tree=ast.parse(Path('qq_notify.py').read_text())
        n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LLM_PROMPT' for t in n.targets))
        prompt=ast.literal_eval(n.value).format(profile='示例学生',today='2026年11月1日',msg='通知')
        self.assertIn('relevant',prompt)
        self.assertIn('示例学生',prompt)
