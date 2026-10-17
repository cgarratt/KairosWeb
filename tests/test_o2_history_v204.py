from o2_history import estimate_post_o1,color_state

def test_provisional_post_o1_not_global_low():
    rows=[{'open_utc':'2026-10-01','high':'0.6','low':'0.1'},
          {'open_utc':'2026-10-02','high':'1.2938','low':'1.1'},
          {'open_utc':'2026-10-03','high':'1.1','low':'0.9600'}]
    h=estimate_post_o1(.964825,.887199,rows)
    assert h['status']=='PROVISIONAL' and h['post_o1_min']==.96
    assert color_state(.964825,h)=='hit'
    assert color_state(.90,h)=='pending'

def test_no_o1_candidate_no_color():
    h=estimate_post_o1(.964825,.887199,[{'open_utc':'2026-10-01','high':'1.0','low':'.5'}])
    assert h['status']=='UNVERIFIED_O1'
    assert color_state(.964825,h)=='unknown'

def test_amber_if_within_one_percent():
    h={'status':'PROVISIONAL','post_o1_min':.9700}
    assert color_state(.964825,h)=='near'
