from o2_history import estimate_post_o1, color_state

def test_no_weekly_o1_date_never_infers_old_fibo():
    rows=[{'open_utc':'2026-10-01','high':'.6','low':'.1'},
          {'open_utc':'2026-10-02','high':'1.2938','low':'1.1'},
          {'open_utc':'2026-10-03','high':'1.1','low':'.9600'}]
    h=estimate_post_o1(.964825,.887199,rows)
    assert h['status']=='WEEKLY_O1_REQUIRED'
    assert color_state(.964825,h)=='unknown'

def test_weekly_selected_o1_allows_only_post_o1_observed_daily_low():
    rows=[{'open_utc':'2026-10-01','high':'.6','low':'.1'},
          {'open_utc':'2026-10-02','high':'1.2938','low':'1.1'},
          {'open_utc':'2026-10-03','high':'1.1','low':'.9600'}]
    h=estimate_post_o1(.964825,.887199,rows,fixed_o1_date='2026-10-02',fixed_o1_price=1.2938)
    assert h['status']=='PROVISIONAL' and h['post_o1_min']==.96
    assert color_state(.964825,h)=='hit'
    assert color_state(.90,h)=='pending'

def test_no_cl_date_no_color():
    h=estimate_post_o1(.964825,.887199,[])
    assert h['status']=='WEEKLY_O1_REQUIRED'
    assert color_state(.964825,h)=='unknown'

def test_amber_if_within_one_percent():
    h={'status':'PROVISIONAL','post_o1_min':.9700}
    assert color_state(.964825,h)=='near'
