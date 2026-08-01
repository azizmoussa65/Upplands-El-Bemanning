from flask import Blueprint, jsonify

from db import companies_col

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/summary")
def summary():
    total_leads = companies_col.count_documents({})

    revenue_agg = list(
        companies_col.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$revenue", 0]}}}}]
        )
    )
    total_revenue = revenue_agg[0]["total"] if revenue_agg else 0

    with_contact = companies_col.count_documents(
        {"$or": [{"bestEmail": {"$nin": [None, ""]}}, {"bestPhone": {"$nin": [None, ""]}}]}
    )

    status_agg = companies_col.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}])
    by_status = {row["_id"]: row["count"] for row in status_agg if row["_id"]}

    top_revenue_docs = (
        companies_col.find({"revenue": {"$ne": None}}, {"name": 1, "revenue": 1, "status": 1})
        .sort("revenue", -1)
        .limit(10)
    )
    top_revenue = [
        {"id": str(d["_id"]), "name": d.get("name"), "revenue": d.get("revenue"), "status": d.get("status")}
        for d in top_revenue_docs
    ]

    to_call_docs = (
        companies_col.find(
            {"status": {"$in": ["nouveau", "a_appeler"]}}, {"name": 1, "aiScore": 1, "revenue": 1}
        )
        .sort([("aiScore", -1), ("revenue", -1)])
        .limit(10)
    )
    priority_to_call = [
        {"id": str(d["_id"]), "name": d.get("name"), "aiScore": d.get("aiScore"), "revenue": d.get("revenue")}
        for d in to_call_docs
    ]

    return jsonify(
        {
            "totalLeads": total_leads,
            "totalRevenue": total_revenue,
            "withContact": with_contact,
            "byStatus": by_status,
            "topRevenue": top_revenue,
            "priorityToCall": priority_to_call,
        }
    )
