"""Audience filtering; no network or calendar side effects."""
import re
import os

PROFILE = os.getenv('STUDENT_PROFILE', '2026级硕士研究生，目前研一（示例身份，请修改）。')
COHORT = int(os.getenv('STUDENT_COHORT', '2026')) % 100

def audience_decision(text, directly_mentioned=False):
    """Return (keep/drop/unknown, reason). Explicit inclusion overrides inference."""
    if directly_mentioned:
        return 'keep', '直接@本人'
    t = re.sub(r'\s+', '', text)
    years = set()
    for m in re.finditer(r'((?:(?:20)?\d{2})(?:[、,，/和及与至到-]*(?:20)?\d{2})*)级', t):
        nums = re.findall(r'20\d{2}|\d{2}', m.group(1))
        years.update(int(n) % 100 for n in nums)
        if len(nums)==2 and re.search(r'[至到-]', m.group(1)):
            years.update(range(int(nums[0])%100,int(nums[1])%100+1))
    # A year in a document title (2026年) is not a cohort.
    inclusive = bool(re.search(r'(全体|所有|各年级|全校|在校).{0,6}(研究生|硕士生|学生|同学|大学生)|研一|研究生一年级', t))
    if re.search(r'有意向|自愿报名|自愿参加|感兴趣的|报名单的.{0,5}位同学|已报名的同学|以上.{0,4}位同学', t) and not re.search(r'必须|务必|均需|全体.{0,5}(参加|到场)', t):
        return 'drop', '自愿活动或指定名单，未确认本人参加'
    if COHORT in years or inclusive:
        return 'keep', '包含26级或全体学生'
    if years:
        return 'drop', '明确面向其他入学年级'
    if re.search(r'研[二三]|研究生[二三]年级|毕业生|应届毕业|博士生', t):
        return 'drop', '其他培养阶段'
    if re.search(r'开题|中期考核|预答辩|毕业答辩|学位申请|毕业资格', t):
        return 'drop', '高年级学位流程且未明确包含研一'
    if re.search(r'(仅限|只限|请|面向|参加人员[：:为]).{0,12}(现代教育技术|学前教育|小学教育|学科教学[（(](语文|数学|英语|化学|生物)[）)])', t):
        return 'drop', '指定其他专业'
    if re.search(r'有意向|自愿报名|自愿参加|感兴趣的|报名单的.{0,5}位同学|已报名的同学|以上.{0,4}位同学', t):
        return 'drop', '自愿活动或指定名单，未确认本人参加'
    return 'unknown', '需结合通知语义判断'
