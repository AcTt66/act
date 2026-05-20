from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user
from app.core.database import (
    add_health_record,
    add_family_member,
    add_checkin,
    add_favorite,
    add_notification,
    add_checkin_task,
    add_health_goal,
    add_health_insight,
    list_health_records,
    list_family_members,
    list_checkins,
    list_checkin_tasks,
    list_favorites,
    list_notifications,
    list_health_goals,
    list_health_insights,
    delete_health_record,
    delete_family_member,
    delete_checkin,
    delete_checkin_task,
    delete_favorite,
    delete_notification,
    mark_notification_read,
    mark_all_notifications_read,
    get_unread_notification_count,
    update_family_member,
    get_health_trends,
    assess_health_data,
    get_health_stats,
    update_health_goal_progress,
    mark_insight_read,
)

router = APIRouter(prefix="/api", tags=["extra_features"])


# ==================== 健康数据记录（增强版）====================

@router.post("/health-records")
async def create_health_record(
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """添加健康数据记录（支持智能评估）"""
    record_type = payload.get("record_type")
    value = payload.get("value")
    value_extra = payload.get("value_extra")
    family_member_id = payload.get("family_member_id")

    # 智能评估
    assessment_result, advice = assess_health_data(record_type, value, value_extra)

    record_id = add_health_record(
        user_id=user["user_id"],
        record_type=record_type,
        value=value,
        value_extra=value_extra,
        unit=payload.get("unit", ""),
        tags=payload.get("tags", ""),
        assessment_result=assessment_result,
        advice=advice,
        note=payload.get("note", ""),
        recorded_at=payload.get("recorded_at") or datetime.now().isoformat(),
        family_member_id=family_member_id,
    )

    # 如果是异常值，生成健康洞察
    if assessment_result in ["高血压", "高血糖", "偏高", "偏低"]:
        add_health_insight(
            user_id=user["user_id"],
            insight_type="warning",
            title=f"{record_type}异常提醒",
            content=f"您的{record_type}记录为{value}{payload.get('unit', '')}，评估结果：{assessment_result}。{advice}",
            data_snapshot=json.dumps({"record_type": record_type, "value": value, "unit": payload.get("unit", "")})
        )

    return {"id": record_id, "ok": True, "assessment": assessment_result, "advice": advice}


@router.get("/health-records")
async def get_health_records(
    record_type: Optional[str] = Query(default=None),
    days: int = Query(default=30),
    family_member_id: Optional[int] = Query(default=None),
    user: dict = Depends(get_current_user)
):
    """获取健康数据记录列表（支持筛选）"""
    records = list_health_records(
        user_id=user["user_id"],
        record_type=record_type,
        days=days,
        family_member_id=family_member_id
    )
    return {"records": records}


@router.get("/health-records/trends")
async def get_health_record_trends(
    record_type: str = Query(...),
    days: int = Query(default=30),
    user: dict = Depends(get_current_user)
):
    """获取健康数据趋势分析"""
    trends = get_health_trends(user_id=user["user_id"], record_type=record_type, days=days)
    return trends


@router.delete("/health-records/{record_id}")
async def remove_health_record(
    record_id: int,
    user: dict = Depends(get_current_user)
):
    """删除健康记录"""
    ok = delete_health_record(record_id=record_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 家庭成员管理（增强版）====================

@router.post("/family-members")
async def create_family_member(
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """添加家庭成员"""
    member_id = add_family_member(
        user_id=user["user_id"],
        name=payload.get("name"),
        gender=payload.get("gender", ""),
        age=payload.get("age", 0),
        relation=payload.get("relation", ""),
        phone=payload.get("phone", ""),
        chronic_diseases=payload.get("chronic_diseases", ""),
        allergy_history=payload.get("allergy_history", ""),
        avatar_color=payload.get("avatar_color", ""),
    )
    return {"id": member_id, "ok": True}


@router.get("/family-members")
async def get_family_members(user: dict = Depends(get_current_user)):
    """获取家庭成员列表（包含健康汇总）"""
    members = list_family_members(user_id=user["user_id"])
    return {"members": members}


@router.put("/family-members/{member_id}")
async def modify_family_member(
    member_id: int,
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """更新家庭成员信息"""
    ok = update_family_member(
        member_id=member_id,
        user_id=user["user_id"],
        name=payload.get("name"),
        gender=payload.get("gender"),
        age=payload.get("age"),
        relation=payload.get("relation"),
        phone=payload.get("phone"),
        chronic_diseases=payload.get("chronic_diseases"),
        allergy_history=payload.get("allergy_history"),
        avatar_color=payload.get("avatar_color"),
        health_summary=payload.get("health_summary"),
    )
    return {"ok": ok}


@router.delete("/family-members/{member_id}")
async def remove_family_member(
    member_id: int,
    user: dict = Depends(get_current_user)
):
    """删除家庭成员"""
    ok = delete_family_member(member_id=member_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 健康打卡（增强版）====================

@router.post("/checkins")
async def create_checkin(
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """添加健康打卡"""
    checkin_type = payload.get("checkin_type")

    # 如果有任务ID，计算连续天数
    task_id = payload.get("checkin_task_id")
    streak_days = 0
    if task_id:
        tasks = list_checkin_tasks(user["user_id"])
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task:
            streak_days = task.get("current_streak", 0)

    checkin_id = add_checkin(
        user_id=user["user_id"],
        family_member_id=payload.get("family_member_id"),
        checkin_type=checkin_type,
        checkin_task_id=task_id,
        status=payload.get("status", "done"),
        streak_days=streak_days,
        note=payload.get("note", ""),
        mood=payload.get("mood", ""),
        weather=payload.get("weather", ""),
        checked_at=payload.get("checked_at") or datetime.now().isoformat(),
    )

    # 根据打卡类型生成健康洞察
    if checkin_type == "运动":
        add_health_insight(
            user_id=user["user_id"],
            insight_type="achievement",
            title="运动打卡完成",
            content=f"太棒了！您完成了今日运动打卡，保持运动习惯对健康非常重要。连续打卡{streak_days + 1}天！",
        )
    elif checkin_type == "服药":
        add_health_insight(
            user_id=user["user_id"],
            insight_type="medication",
            title="服药提醒",
            content="记得按时服药哦！规律服药对疾病管理很重要。",
        )

    return {"id": checkin_id, "ok": True, "streak_days": streak_days + 1}


@router.get("/checkins")
async def get_checkins(
    days: int = Query(default=30),
    family_member_id: Optional[int] = Query(default=None),
    checkin_type: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user)
):
    """获取健康打卡列表"""
    checkins = list_checkins(
        user_id=user["user_id"],
        days=days,
        family_member_id=family_member_id,
        checkin_type=checkin_type,
    )
    return {"checkins": checkins}


@router.delete("/checkins/{checkin_id}")
async def remove_checkin(
    checkin_id: int,
    user: dict = Depends(get_current_user)
):
    """删除健康打卡"""
    ok = delete_checkin(checkin_id=checkin_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 打卡任务/习惯 ====================

@router.post("/checkin-tasks")
async def create_checkin_task(
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """添加打卡任务"""
    task_id = add_checkin_task(
        user_id=user["user_id"],
        family_member_id=payload.get("family_member_id"),
        task_name=payload.get("task_name"),
        task_type=payload.get("task_type"),
        target_days=payload.get("target_days", ""),
        reminder_time=payload.get("reminder_time", ""),
        reminder_enabled=payload.get("reminder_enabled", False),
    )
    return {"id": task_id, "ok": True}


@router.get("/checkin-tasks")
async def get_checkin_tasks(
    active_only: bool = Query(default=True),
    user: dict = Depends(get_current_user)
):
    """获取打卡任务列表"""
    tasks = list_checkin_tasks(user_id=user["user_id"], active_only=active_only)
    return {"tasks": tasks}


@router.delete("/checkin-tasks/{task_id}")
async def remove_checkin_task(
    task_id: int,
    user: dict = Depends(get_current_user)
):
    """删除打卡任务"""
    ok = delete_checkin_task(task_id=task_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 收藏（增强版）====================

@router.post("/favorites")
async def create_favorite(
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """添加收藏"""
    fav_id = add_favorite(
        user_id=user["user_id"],
        fav_type=payload.get("fav_type"),
        target_id=payload.get("target_id", ""),
        title=payload.get("title", ""),
        content=payload.get("content", ""),
        tags=payload.get("tags", ""),
        related_record_id=payload.get("related_record_id"),
        related_member_id=payload.get("related_member_id"),
        color=payload.get("color", ""),
    )
    return {"id": fav_id, "ok": True}


@router.get("/favorites")
async def get_favorites(
    fav_type: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user)
):
    """获取收藏列表"""
    favorites = list_favorites(user_id=user["user_id"], fav_type=fav_type, tags=tags)
    return {"favorites": favorites}


@router.delete("/favorites/{favorite_id}")
async def remove_favorite(
    favorite_id: int,
    user: dict = Depends(get_current_user)
):
    """删除收藏"""
    ok = delete_favorite(favorite_id=favorite_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 消息通知（增强版）====================

@router.get("/notifications")
async def get_notifications(
    include_read: bool = Query(default=True),
    notif_type: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user)
):
    """获取消息通知列表"""
    notifications = list_notifications(
        user_id=user["user_id"],
        include_read=include_read,
        notif_type=notif_type,
    )
    unread_count = get_unread_notification_count(user_id=user["user_id"], notif_type=notif_type)
    return {"notifications": notifications, "unread_count": unread_count}


@router.post("/notifications/{notif_id}/read")
async def mark_read(
    notif_id: int,
    user: dict = Depends(get_current_user)
):
    """标记通知为已读"""
    ok = mark_notification_read(notif_id=notif_id, user_id=user["user_id"])
    return {"ok": ok}


@router.post("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """标记所有通知为已读"""
    count = mark_all_notifications_read(user_id=user["user_id"])
    return {"count": count, "ok": True}


@router.delete("/notifications/{notif_id}")
async def remove_notification(
    notif_id: int,
    user: dict = Depends(get_current_user)
):
    """删除通知"""
    ok = delete_notification(notif_id=notif_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 健康目标 ====================

@router.post("/health-goals")
async def create_health_goal(
    payload: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """添加健康目标"""
    goal_id = add_health_goal(
        user_id=user["user_id"],
        goal_name=payload.get("goal_name"),
        goal_type=payload.get("goal_type"),
        target_value=payload.get("target_value"),
        unit=payload.get("unit", ""),
        deadline=payload.get("deadline", ""),
        family_member_id=payload.get("family_member_id"),
    )
    return {"id": goal_id, "ok": True}


@router.get("/health-goals")
async def get_health_goals(
    active_only: bool = Query(default=True),
    user: dict = Depends(get_current_user)
):
    """获取健康目标列表"""
    goals = list_health_goals(user_id=user["user_id"], active_only=active_only)
    return {"goals": goals}


@router.put("/health-goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: int,
    current_value: float = Query(...),
    user: dict = Depends(get_current_user)
):
    """更新健康目标进度"""
    ok = update_health_goal_progress(goal_id=goal_id, current_value=current_value, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 健康洞察 ====================

@router.get("/health-insights")
async def get_health_insights(
    unread_only: bool = Query(default=False),
    user: dict = Depends(get_current_user)
):
    """获取健康洞察列表"""
    insights = list_health_insights(user_id=user["user_id"], unread_only=unread_only)
    return {"insights": insights}


@router.post("/health-insights/{insight_id}/read")
async def mark_insight_read(
    insight_id: int,
    user: dict = Depends(get_current_user)
):
    """标记洞察为已读"""
    ok = mark_insight_read(insight_id=insight_id, user_id=user["user_id"])
    return {"ok": ok}


# ==================== 健康统计 ====================

@router.get("/health-stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """获取健康数据统计"""
    stats = get_health_stats(user_id=user["user_id"])
    return stats


# ==================== 辅助工具（增强版）====================

@router.get("/tools/bmi")
async def calculate_bmi(
    height: float = Query(..., description="身高（cm）"),
    weight: float = Query(..., description="体重（kg）"),
    save_to_records: bool = Query(default=False, description="是否保存到健康记录"),
    user: dict = Depends(get_current_user)
):
    """BMI计算器（可一键保存）"""
    height_m = height / 100
    bmi = weight / (height_m * height_m)
    bmi = round(bmi, 1)

    if bmi < 18.5:
        category = "偏瘦"
        advice = "建议适当增加营养摄入，保持均衡饮食。多吃蛋白质和复合碳水化合物。"
    elif bmi < 24:
        category = "正常"
        advice = "继续保持健康的生活方式。保持适量运动和均衡饮食。"
    elif bmi < 28:
        category = "偏胖"
        advice = "建议适当控制饮食，增加运动量。减少高热量食物摄入。"
    else:
        category = "肥胖"
        advice = "建议咨询医生，制定科学的减重计划。控制饮食，增加运动，必要时寻求专业帮助。"

    result = {
        "bmi": bmi,
        "category": category,
        "advice": advice,
        "height": height,
        "weight": weight
    }

    # 一键保存到健康记录
    if save_to_records:
        record_id = add_health_record(
            user_id=user["user_id"],
            record_type="体重",
            value=weight,
            unit="kg",
            tags="bmi",
            assessment_result=f"BMI {bmi} ({category})",
            advice=advice,
            note=f"身高{height}cm计算"
        )
        result["saved_record_id"] = record_id

    return result


@router.get("/tools/blood-pressure")
async def eval_blood_pressure(
    systolic: int = Query(..., description="收缩压（mmHg）"),
    diastolic: int = Query(..., description="舒张压（mmHg）"),
    save_to_records: bool = Query(default=False, description="是否保存到健康记录"),
    user: dict = Depends(get_current_user)
):
    """血压评估工具（可一键保存）"""
    if systolic < 120 and diastolic < 80:
        category = "正常"
        advice = "血压保持在健康范围内，请继续保持良好的生活习惯。"
    elif systolic < 130 and diastolic < 80:
        category = "偏高"
        advice = "血压略高于正常值，建议减少盐分摄入，适量运动，保持充足睡眠。"
    elif systolic < 140 or diastolic < 90:
        category = "高血压前期"
        advice = "血压处于高血压前期，建议积极改善生活方式，减少高脂肪食物摄入，避免情绪激动。如有不适请及时就医。"
    elif systolic >= 140 or diastolic >= 90:
        category = "高血压"
        advice = "血压明显升高，建议尽快就医，根据医生建议进行管理和治疗。避免高盐高脂饮食，戒烟限酒。"
    else:
        category = "需进一步评估"
        advice = "建议咨询医生获取专业建议。"

    result = {
        "systolic": systolic,
        "diastolic": diastolic,
        "category": category,
        "advice": advice
    }

    # 一键保存到健康记录
    if save_to_records:
        # 智能评估
        assessment_result, auto_advice = assess_health_data("血压", float(systolic), float(diastolic))
        record_id = add_health_record(
            user_id=user["user_id"],
            record_type="血压",
            value=float(systolic),
            value_extra=float(diastolic),
            unit="mmHg",
            tags="tool",
            assessment_result=assessment_result,
            advice=auto_advice,
            note="血压评估工具记录"
        )
        result["saved_record_id"] = record_id

        # 如果异常，生成通知
        if category in ["高血压前期", "高血压", "偏高"]:
            add_notification(
                user_id=user["user_id"],
                title="血压异常提醒",
                content=f"您的血压为{systolic}/{diastolic}mmHg，评估结果：{category}。{advice}",
                notif_type="health_warning",
                priority="high"
            )

    return result


@router.get("/tools/blood-sugar")
async def eval_blood_sugar(
    value: float = Query(..., description="空腹血糖（mmol/L）"),
    save_to_records: bool = Query(default=False, description="是否保存到健康记录"),
    user: dict = Depends(get_current_user)
):
    """血糖评估工具"""
    if value < 3.9:
        category = "偏低"
        advice = "血糖偏低，建议及时补充糖分，适当增加碳水化合物摄入。如有频繁发生请咨询医生。"
    elif value < 6.1:
        category = "正常"
        advice = "空腹血糖在正常范围内，请继续保持均衡饮食和适量运动。"
    elif value < 7.0:
        category = "偏高"
        advice = "空腹血糖偏高，处于糖尿病前期阶段。建议控制饮食，减少糖分摄入，增加运动量，并定期监测血糖。"
    else:
        category = "高血糖"
        advice = "空腹血糖明显升高，糖尿病风险较高。建议尽早就医检查，按医嘱进行饮食控制和必要治疗。"

    result = {
        "value": value,
        "category": category,
        "advice": advice
    }

    if save_to_records:
        assessment_result, auto_advice = assess_health_data("血糖", value)
        record_id = add_health_record(
            user_id=user["user_id"],
            record_type="血糖",
            value=value,
            unit="mmol/L",
            tags="tool",
            assessment_result=assessment_result,
            advice=auto_advice,
            note="血糖评估工具记录"
        )
        result["saved_record_id"] = record_id

        if category in ["偏高", "高血糖", "偏低"]:
            add_notification(
                user_id=user["user_id"],
                title="血糖异常提醒",
                content=f"您的空腹血糖为{value}mmol/L，评估结果：{category}。{advice}",
                notif_type="health_warning",
                priority="high"
            )

    return result

@router.get("/tools/blood-glucose")
async def eval_blood_glucose(
    value: float = Query(..., description="血糖值（mmol/L）"),
    time_of_day: str = Query(default="空腹", description="测量时间：空腹、餐后2小时、随机"),
    save_to_records: bool = Query(default=False, description="是否保存到健康记录"),
    user: dict = Depends(get_current_user)
):
    """血糖评估工具（增强版，支持不同测量时间）"""
    if time_of_day == "空腹":
        if value < 3.9:
            category = "偏低"
            advice = "血糖偏低，建议及时补充糖分，适当增加碳水化合物摄入。如有频繁发生请咨询医生。"
        elif value < 6.1:
            category = "正常"
            advice = "空腹血糖在正常范围内，请继续保持均衡饮食和适量运动。"
        elif value < 7.0:
            category = "偏高"
            advice = "空腹血糖偏高，处于糖尿病前期阶段。建议控制饮食，减少糖分摄入，增加运动量，并定期监测血糖。"
        else:
            category = "高血糖"
            advice = "空腹血糖明显升高，糖尿病风险较高。建议尽早就医检查，按医嘱进行饮食控制和必要治疗。"
    elif time_of_day == "餐后2小时":
        if value < 7.8:
            category = "正常"
            advice = "餐后2小时血糖正常，请继续保持健康的饮食习惯。"
        elif value < 11.1:
            category = "糖耐量减低"
            advice = "餐后血糖偏高，建议控制饮食量，减少精制碳水摄入，餐后适当运动。"
        else:
            category = "高血糖"
            advice = "餐后2小时血糖明显升高，建议咨询医生进行进一步检查。"
    else:
        if value < 11.1:
            category = "正常"
            advice = "随机血糖正常，请继续保持良好的生活习惯。"
        else:
            category = "高血糖"
            advice = "随机血糖较高，建议进行空腹血糖检测以进一步评估。"

    result = {
        "value": value,
        "time_of_day": time_of_day,
        "category": category,
        "advice": advice
    }

    if save_to_records:
        assessment_result, auto_advice = assess_health_data("血糖", value)
        record_id = add_health_record(
            user_id=user["user_id"],
            record_type="血糖",
            value=value,
            unit="mmol/L",
            tags="tool",
            assessment_result=assessment_result,
            advice=auto_advice,
            note=f"血糖评估工具记录（{time_of_day}）"
        )
        result["saved_record_id"] = record_id

    return result
