import unittest
from qq_relevance import audience_decision
class AudienceTests(unittest.TestCase):
    def test_examples(self):
        for text,want in [('请24、25级提交材料','drop'),('242526级均需到场','keep'),('请26级提交开题表','keep'),('2026年学位论文中期考核通知','drop'),('全体研究生参加会议','keep'),('有意向参赛的同学自愿报名','drop'),('请研二提交材料','drop'),('医保缴费截止明天','unknown')]:
            with self.subTest(text=text):self.assertEqual(audience_decision(text)[0],want)
    def test_direct_mention(self):self.assertEqual(audience_decision('研二通知',True)[0],'keep')
