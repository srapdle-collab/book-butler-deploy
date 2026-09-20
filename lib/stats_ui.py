from datetime import datetime,date
from zoneinfo import ZoneInfo
import streamlit as st
from lib.statistics import summarize


def render(conn):
    st.header('📊 통계')
    today=datetime.now(ZoneInfo('Asia/Seoul')).date()
    st.caption('한국 시간 기준 · 미래 날짜 제외 · 삭제된 기록 제외')
    st.subheader('일별 독서 · 기본: 이번 달')
    period=st.date_input('일별 통계 기간',value=(today.replace(day=1),today),min_value=date(1900,1,1),max_value=today,key='daily_period')
    if len(period)==2:
        result=summarize(conn,*period)
        columns=st.columns(3)
        columns[0].metric('읽은 쪽수',f"{result['pages']:g}")
        columns[1].metric('평균 쪽/일',f"{result['pages_per_day']:.1f}")
        columns[2].metric('평균 분/일',f"{result['minutes_per_day']:.1f}")
        metric=st.radio('일별 그래프',['쪽수','시간'],horizontal=True,key='daily_metric')
        st.bar_chart(result['daily'][['pages' if metric=='쪽수' else 'minutes']].rename(columns={'pages':'쪽수','minutes':'분'}))
        st.caption(f"평균 = 선택 기간의 합계 ÷ {result['days']}일. 시작일·종료일과 기록 없는 날을 모두 포함합니다.")
    else: st.info('시작일과 종료일을 선택해주세요.')
    st.subheader('월별 독서 · 기본: 올해')
    period=st.date_input('월별 통계 기간',value=(today.replace(month=1,day=1),today),min_value=date(1900,1,1),max_value=today,key='monthly_period')
    if len(period)==2:
        result=summarize(conn,*period)
        columns=st.columns(3)
        columns[0].metric('완독 횟수',str(result['finishes']))
        columns[1].metric('평균 권/월',f"{result['books_per_month']:.1f}")
        columns[2].metric('평균 쪽/월',f"{result['pages']/result['months']:.1f}")
        metric=st.radio('월별 그래프',['책','쪽수','시간'],horizontal=True,key='monthly_metric')
        column={'책':'finishes','쪽수':'pages','시간':'minutes'}[metric]
        st.bar_chart(result['monthly'][[column]].rename(columns={column:metric}))
        st.caption(f"평균 = 선택 기간의 합계 ÷ 걸쳐 있는 {result['months']}개 달. 일부 날짜만 선택된 달도 1개월입니다. 재독 완독도 1회씩 셉니다.")
    else: st.info('시작일과 종료일을 선택해주세요.')
    st.caption('쪽수는 진도 기록의 실제 읽은 쪽수, 시간은 저장된 초/60(원본은 분)을 합산합니다. 음수·누락 측정값은 합계에서 0으로 처리하고 원본 값은 보존합니다. 평균 표시는 소수 첫째 자리로 반올림합니다.')
    st.caption('원본 kind=5는 독서 시작이므로 완독 수에서 제외합니다. 원본 kind=6(별점 동반 완료)과 새 앱의 완료 이벤트를 합산합니다.')
