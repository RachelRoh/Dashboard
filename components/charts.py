import plotly.express as px
import pandas as pd


STATUS_COLORS = {
    "가용": "#4CAF50",
    "고장": "#FF5722",
    "폐기": "#9E9E9E",
}


PASTEL_COLORS = [
    "#FFCDD2",  # 핑크
    "#BBDEFB",  # 파랑
    "#FFF9C4",  # 노랑
    "#C8E6C9",  # 초록
    "#F8BBD0",  # 로즈
    "#B2EBF2",  # 하늘
    "#FFECB3",  # 앰버
    "#E1BEE7",  # 보라
    "#DCEDC8",  # 연두
    "#FFE0B2",  # 복숭아
]


def pie_model_total(df: pd.DataFrame):
    """모델별 전체 수량 파이 차트"""
    fig = px.pie(
        df,
        names="모델",
        values="전체",
        color_discrete_sequence=PASTEL_COLORS,
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(orientation="v", x=1.02, y=0.5),
        showlegend=True,
    )
    return fig


def bar_status_by_model(df: pd.DataFrame):
    """모델별 상태 스택 바 차트"""
    status_cols = [c for c in ["가용", "고장", "폐기"] if c in df.columns]
    melted = df.melt(
        id_vars="모델", value_vars=status_cols,
        var_name="상태", value_name="수량",
    )
    fig = px.bar(
        melted,
        x="모델",
        y="수량",
        color="상태",
        color_discrete_map=STATUS_COLORS,
        barmode="stack",
    )
    fig.update_layout(
        xaxis_tickangle=-30,
        margin=dict(t=30, b=60, l=10, r=10),
        legend_title_text="상태",
    )
    return fig


def bar_team_equipment(df: pd.DataFrame):
    """팀별 모델 수량 그룹 바 차트"""
    fig = px.bar(
        df,
        x="팀",
        y="수량",
        color="모델",
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        margin=dict(t=30, b=40, l=10, r=10),
        legend_title_text="모델",
    )
    return fig


def pie_team_share(df: pd.DataFrame, team: str):
    """특정 팀의 모델별 보유 비율 파이 차트"""
    team_df = df[df["팀"] == team]
    fig = px.pie(
        team_df,
        names="모델",
        values="수량",
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(t=30, b=10, l=10, r=10), showlegend=True)
    return fig
