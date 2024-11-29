from decimal import Decimal, getcontext
from django.db import transaction
from django.db.models import Sum
from .models import Milestone

import logging

logger = logging.getLogger(__name__)

def recalculate_milestone_points(project):
    logger.debug(f"Recalculating points for project {project.id}")
    with transaction.atomic():
        getcontext().prec = 10  # 小数点の精度を設定

        # 全てのリーフマイルストーン（子のないマイルストーン）を取得
        leaf_milestones = Milestone.objects.filter(goal__project=project, child_milestones__isnull=True)

        if not leaf_milestones.exists():
            return  # リーフマイルストーンがない場合は処理を終了

        # 手動設定ポイントがNULLのマイルストーンの数を取得
        auto_point_milestones = leaf_milestones.filter(manual_points__isnull=True)
        num_auto_points = auto_point_milestones.count()

        # 自動設定ポイントを計算
        if num_auto_points > 0:
            auto_point_value = project.total_investment / num_auto_points
        else:
            auto_point_value = Decimal('0.0')

        # リーフマイルストーンのポイントを設定
        for milestone in leaf_milestones:
            if milestone.manual_points is not None:
                # 手動設定ポイントがある場合
                milestone.auto_points = None
                milestone.points = milestone.manual_points
            else:
                # 手動設定ポイントがない場合、自動設定ポイントを割り当て
                milestone.auto_points = auto_point_value
                milestone.points = auto_point_value
            milestone.save()

        # 親マイルストーンのポイントを再帰的に計算
        _update_parent_points(project)

        # 総投資額を更新（末端マイルストーンのポイントの合計）
        total_points = leaf_milestones.aggregate(total_points=Sum('points'))['total_points'] or Decimal('0.0')
        project.total_investment = total_points
        project.save()

def _update_parent_points(project):
    # 親マイルストーンを階層の下位から順に取得
    parent_milestones = Milestone.objects.filter(goal__project=project).exclude(child_milestones__isnull=True).order_by('-id')
    for milestone in parent_milestones:
        # 子マイルストーンのポイント合計を計算
        total_child_points = milestone.child_milestones.aggregate(
            total_points=Sum('points')
        )['total_points'] or Decimal('0.0')

        # 親マイルストーンのポイントを更新
        milestone.points = total_child_points
        milestone.save()

def adjust_milestone_points_on_investment_change(project, new_investment):
    with transaction.atomic():
        # リーフマイルストーンの ID を取得
        leaf_milestone_ids = list(Milestone.objects.filter(
            goal__project=project,
            child_milestones__isnull=True
        ).values_list('id', flat=True))

        if not leaf_milestone_ids:
            return

        # ID を使用してマイルストーンを取得し、ロックを適用
        leaf_milestones = Milestone.objects.filter(
            id__in=leaf_milestone_ids
        ).select_for_update()

        total_points = leaf_milestones.aggregate(
            total_points=Sum('points')
        )['total_points'] or Decimal('0.0')

        difference = new_investment - total_points
        num_leaf_milestones = len(leaf_milestone_ids)

        if num_leaf_milestones == 0:
            return

        adjustment = difference / num_leaf_milestones

        # ポイントがマイナスになるかチェック
        for milestone in leaf_milestones:
            new_point = milestone.points + adjustment
            if new_point < 0:
                raise ValueError("ポイントがマイナスになるため、調整できません。")

        # ポイントを調整し、manual_pointsとして登録
        for milestone in leaf_milestones:
            new_point = milestone.points + adjustment
            milestone.manual_points = new_point
            milestone.points = new_point
            milestone.auto_points = None
            milestone.save()

        # 親マイルストーンのポイントを再計算
        _update_parent_points(project)

        # 総投資額を更新
        project.total_investment = new_investment
        project.save()