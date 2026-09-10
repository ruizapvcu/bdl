import streamlit as st

from src.analyze import get_conference_standings, get_standings_history
from src.wrapper import call_ai


st.set_page_config(page_title="NCAAF Standings")
st.title("NCAAF Standings")

selected_season = st.number_input(
    "Season", min_value=2000, max_value=2100, value=2026, step=1
)
standings = get_conference_standings(int(selected_season))

if standings.empty:
    st.info(f"No standings found for the {int(selected_season)} season.")
    st.stop()

selected_conference = st.selectbox(
    "Conference",
    ["All Conferences"] + sorted(standings["conference"].unique()),
)
team_source = standings
if selected_conference != "All Conferences":
    team_source = standings[standings["conference"] == selected_conference]
team_labels = {
    f"{row.city} {row.name} ({row.abbreviation})": row.team_id
    for row in team_source.itertuples()
}
selected_team = st.selectbox("Team", ["All Teams"] + sorted(team_labels))

conference_standings = standings.copy()
if selected_conference != "All Conferences":
    conference_standings = conference_standings[
        conference_standings["conference"] == selected_conference
    ]
if selected_team != "All Teams":
    conference_standings = conference_standings[
        conference_standings["team_id"] == team_labels[selected_team]
    ]

st.dataframe(
    conference_standings,
    hide_index=True,
    use_container_width=True,
    column_config={
        "logo_url": st.column_config.ImageColumn("Helmet", width="small"),
        "name": st.column_config.TextColumn("Mascot"),
    },
)

st.subheader("Season progress")
history = get_standings_history(int(selected_season))
if history.empty:
    st.info("No historical snapshots are available for this season.")
else:
    dates = sorted(history["snapshot_date"].unique())
    selected_date = st.select_slider("Snapshot date", options=dates, value=dates[-1])
    progress = history[history["snapshot_date"] == selected_date].copy()
    history["conference_place"] = history.groupby(
        ["snapshot_date", "conference"]
    )["wins"].rank(method="min", ascending=False).astype(int)
    history["overall_place"] = history.groupby("snapshot_date")["wins"].rank(
        method="min", ascending=False
    ).astype(int)
    progress = history[history["snapshot_date"] == selected_date].copy()
    if selected_conference != "All Conferences":
        progress = progress[progress["conference"] == selected_conference]
    progress = progress.sort_values(["conference", "conference_place", "city"])
    st.caption("Teams are ordered by wins, then losses and city. Select a date to compare snapshots.")
    st.dataframe(
        progress[
            [
                "logo_url",
                "conference",
                "city",
                "name",
                "wins",
                "losses",
                "conference_place",
                "overall_place",
            ]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "logo_url": st.column_config.ImageColumn("Helmet", width="small"),
            "name": st.column_config.TextColumn("Mascot"),
        },
    )

    chart_history = history.copy()
    if selected_conference != "All Conferences":
        chart_history = chart_history[
            chart_history["conference"] == selected_conference
        ]
    if selected_team != "All Teams":
        chart_history = chart_history[
            chart_history["team_id"] == team_labels[selected_team]
        ]
    chart_history["team"] = chart_history["city"] + " " + chart_history["name"]
    rank_chart = chart_history.pivot_table(
        index="snapshot_date", columns="team", values="conference_place"
    ).sort_index()
    if not rank_chart.empty:
        st.caption("Conference rank over time. Rank 1 is the best position.")
        st.line_chart(rank_chart, y_label="Conference rank", x_label="Snapshot date")

st.divider()
st.subheader("AI snapshot assistant")
st.caption("The assistant receives the latest non-legacy snapshot for the selected season.")

if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []

if st.button("Summarize latest snapshot", type="primary"):
    with st.spinner("Reading the latest database snapshot..."):
        try:
            summary = call_ai(
                "Summarize the latest standings snapshot. Mention the snapshot date, "
                "the conferences included, and notable leaders or records.",
                int(selected_season),
            )
            st.session_state.ai_messages.append(
                {"role": "assistant", "content": summary}
            )
        except RuntimeError as error:
            st.error(str(error))

for message in st.session_state.ai_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about the latest standings snapshot"):
    history = st.session_state.ai_messages.copy()
    st.session_state.ai_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Asking the AI service..."):
            try:
                answer = call_ai(prompt, int(selected_season), history)
                st.markdown(answer)
                st.session_state.ai_messages.append(
                    {"role": "assistant", "content": answer}
                )
            except RuntimeError as error:
                st.error(str(error))