from typing import NamedTuple
from math import ceil
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .forms import ExperimentForm
from simulate import experiment,choose_best,daily_result
from . import configuration


class ChartGeometry(NamedTuple):
    left: int
    width: int
    baseline: int
    height: int


CHART = ChartGeometry(left=45, width=690, baseline=220, height=190)
TRACE_PAGE_SIZE = 100


def context(form,c=None,selected=None,trace_page=None):
    ctx={"form":form}
    if c:
        selected = configuration.default_stock(c) if selected is None else selected
        result=experiment(c);rows=result[0]
        best=choose_best(rows,"sim_textbook_score")
        cash_best=choose_best(rows,"sim_cash_profit")
        chosen=next(r for r in rows if r["stock"]==selected)
        summary,per_run,trace,_,_=result
        page=Paginator(trace,TRACE_PAGE_SIZE).get_page(trace_page)
        ctx.update(summary_rows=summary,
                   run_rows=[r for r in per_run if r["stock"]==selected],
                   audit_rows=[{**day, "stock":selected, **daily_result(selected,day["demand"],c)}
                               for day in trace[:c["audit_days"]]],
                   trace_page=page,trace_requested=trace_page is not None,
                   run_count=c["runs"],days_per_run=c["days_per_run"])
        lo=min(0,min(r["sim_textbook_score"] for r in rows));hi=max(1,max(r["sim_textbook_score"] for r in rows));span=max(1,hi-lo)
        def points(key):return " ".join(f"{CHART.left+i*CHART.width/max(1,len(rows)-1):.2f},{CHART.baseline-(r[key]-lo)*CHART.height/span:.2f}" for i,r in enumerate(rows))
        label_stride=max(1,ceil((len(rows)-1)/10))
        ctx.update(selected=selected,result=result,best=", ".join(map(str,best)),cash_best=", ".join(map(str,cash_best)),chosen=chosen,
                   sim_points=points("sim_textbook_score"),exact_points=points("exact_textbook_score"),
                   ticks=[{"value":round(lo+i*span/4,1),"y":CHART.baseline-i*CHART.height/4} for i in range(5)],
                   xticks=[{"value":r["stock"],"x":CHART.left+i*CHART.width/max(1,len(rows)-1)} for i,r in enumerate(rows) if i % label_stride == 0 or i == len(rows)-1],
                   view_values={**{k:v for k,v in configuration.initial(c).items() if k in form.fields},"chosen_stock":selected},count=c["runs"]*c["days_per_run"])
    return ctx
@require_http_methods(["GET","POST"])
def index(request):
    if request.method=="POST":
        form=ExperimentForm(request.POST)
        if not form.is_valid():return render(request,"simulator/index.html",context(form),status=400)
        c=form.cleaned_data["config"]
    else:c=configuration.defaults();form=ExperimentForm(initial=configuration.initial(c),config=c)
    return render(request,"simulator/index.html",context(form,c,form.cleaned_data["chosen_stock"] if request.method=="POST" else None,request.POST.get("trace_page") if request.method=="POST" else request.GET.get("trace_page")))
