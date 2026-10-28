"""Chronology contract shared by KairosGPT and KairosWeb. No side effects."""
from datetime import date

ORDER=('cl','o1','o2','o3','o4','o5')

def timeline_issues(pivots):
    """Dated pivots form a strict, consecutive CL -> O5 prefix.

    Undated PROPUESTO prices are projections, not dated structural pivots.
    An invalid inherited row remains readable for repair, never usable as anchors.
    """
    rows={'cl':{'price':pivots.get('cycle_low'),'date':pivots.get('cl_date')}}
    rows.update(pivots.get('waves') or {})
    issues=[];previous=None
    for index,wave in enumerate(ORDER):
        item=rows.get(wave) or {};day=item.get('date')
        if not day:continue
        try:
            if not isinstance(day,str) or date.fromisoformat(day).isoformat()!=day:raise ValueError()
        except (ValueError,TypeError):
            issues.append(f'{wave.upper()}: fecha UTC inválida');continue
        if item.get('price') in (None,''):
            issues.append(f'{wave.upper()}: fecha sin precio')
        if index and not (rows.get(ORDER[index-1]) or {}).get('date'):
            issues.append(f'{wave.upper()}: falta fecha de {ORDER[index-1].upper()} anterior')
        if previous and day<=previous[1]:
            issues.append(f'{wave.upper()} ({day}) debe ser posterior a {previous[0].upper()} ({previous[1]})')
        previous=(wave,day)
    return issues

def require_timeline(pivots, token=''):
    issues=timeline_issues(pivots)
    if issues:raise ValueError((str(token)+' · ' if token else '')+'Cronología inválida: '+'; '.join(issues))
    return pivots
