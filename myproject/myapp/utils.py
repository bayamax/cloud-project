# utils.py

from decimal import Decimal
from django.db import transaction

def recalculate_milestone_points(goal):
    with transaction.atomic():
        all_milestones = goal.milestones.all()
        num_top_level = all_milestones.filter(parent_milestone__isnull=True).count()
        if num_top_level == 0:
            return  # マイルストーンがない場合は処理を終了

        points_per_top_level = Decimal('1.0') / num_top_level

        # トップレベルのマイルストーンを更新
        for milestone in all_milestones.filter(parent_milestone__isnull=True):
            milestone.points = points_per_top_level
            milestone.save()
            _update_child_points(milestone)

def _update_child_points(parent_milestone):
    child_milestones = parent_milestone.child_milestones.all()
    num_children = child_milestones.count()
    if num_children == 0:
        return

    points_per_child = parent_milestone.points / num_children

    for child in child_milestones:
        child.points = points_per_child
        child.save()
        # 再帰的に子マイルストーンを更新
        _update_child_points(child)