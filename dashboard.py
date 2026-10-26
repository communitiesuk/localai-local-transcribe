import os
import subprocess
import time
import urllib.request
import psycopg2
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Local Transcribe Quick Insights Hub", layout="wide")

# --- Configuration ---
AWS_PROFILE_NAME = "robb-lt-prod"
ENV = st.sidebar.selectbox("Select Environment", ["production", "development"], index=0)
PORT = "5433"
REGION = "eu-west-2"
SCRIPT_PATH = "./connect-to-aws-db.sh"

CA_DIR = os.path.expanduser("~/.cache/local-transcribe")
CA_PATH = os.path.join(CA_DIR, f"rds-ca-bundle-{REGION}.pem")

# MHCLG logo, inlined from frontend/components/icons/mhclg-logo.tsx so both the
# dashboard and the standalone HTML report stay self-contained (no asset loading).
# fill="currentColor" means it picks up whatever text colour it sits in.
MHCLG_LOGO_PATH = (
    "M33.1,9.8c.2-.1.3-.3.5-.5l4.6,2.4v-6.8l-4.6,1.5c-.1-.2-.3-.3-.5-.5l1.9-5.9h-6.7l1.9,5.9c-.2.1-.3.3-.5.5"
    "l-4.6-1.5v6.8l4.6-2.4c.1.2.3.3.5.5l-2.6,8c-.9,2.8,1.2,5.7,4.1,5.7h0c3,0,5.1-2.9,4.1-5.7l-2.6-8ZM37,37.9"
    "s-3.4,3.8-4.1,6.1c2.2,0,4.2-.5,6.4-2.8l-.7,8.5c-2-2.8-4.4-4.1-5.7-3.8.1,3.1.5,6.7,5.8,7.2,3.7.3,6.7-1.5,7-3.8"
    ".4-2.6-2-4.3-3.7-1.6-1.4-4.5,2.4-6.1,4.9-3.2-1.9-4.5-1.8-7.7,2.4-10.9,3,4,2.6,7.3-1.2,11.1,2.4-1.3,6.2,0,4,4.6"
    "-1.2-2.8-3.7-2.2-4.2.2-.3,1.7.7,3.7,3,4.2,1.9.3,4.7-.9,7-5.9-1.3,0-2.4.7-3.9,1.7l2.4-8c.6,2.3,1.4,3.7,2.2,4.5"
    ".6-1.6.5-2.8,0-5.3l5,1.8c-2.6,3.6-5.2,8.7-7.3,17.5-7.4-1.1-15.7-1.7-24.5-1.7h0c-8.8,0-17.1.6-24.5,1.7"
    "-2.1-8.9-4.7-13.9-7.3-17.5l5-1.8c-.5,2.5-.6,3.7,0,5.3.8-.8,1.6-2.3,2.2-4.5l2.4,8c-1.5-1-2.6-1.7-3.9-1.7"
    ",2.3,5,5.2,6.2,7,5.9,2.3-.4,3.3-2.4,3-4.2-.5-2.4-3-3.1-4.2-.2-2.2-4.6,1.6-6,4-4.6-3.7-3.7-4.2-7.1-1.2-11.1"
    ",4.2,3.2,4.3,6.4,2.4,10.9,2.5-2.8,6.3-1.3,4.9,3.2-1.8-2.7-4.1-1-3.7,1.6.3,2.3,3.3,4.1,7,3.8,5.4-.5,5.7-4.2,5.8-7.2"
    "-1.3-.2-3.7,1-5.7,3.8l-.7-8.5c2.2,2.3,4.2,2.7,6.4,2.8-.7-2.3-4.1-6.1-4.1-6.1h10.6,0Z"
)

MHCLG_LOGO_CIRCLES = [
    (20, 17.6), (10.2, 23.5), (3.7, 33.2), (31.7, 30.6),
    (43.3, 17.6), (53.2, 23.5), (59.7, 33.2),
]

def mhclg_logo_svg(width=32, height=30):
    circles = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="3.7" />' for cx, cy in MHCLG_LOGO_CIRCLES
    )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 64 60" fill="currentColor" '
        f'focusable="false" aria-hidden="true" style="flex-shrink:0;">'
        f'{circles}<path d="{MHCLG_LOGO_PATH}" /></svg>'
    )

def ensure_rds_cert():
    if not os.path.exists(CA_PATH):
        os.makedirs(CA_DIR, exist_ok=True)
        url = f"https://truststore.pki.rds.amazonaws.com/{REGION}/{REGION}-bundle.pem"
        urllib.request.urlretrieve(url, CA_PATH)

# --- Updated Queries ---

# 1. Total Transcriptions per Council
QUERY_TRANSCRIPTIONS = """
SELECT
  CASE
    WHEN evaluation_id ILIKE '%HAR%' THEN 'Hart'
    WHEN evaluation_id ILIKE '%BIR%' THEN 'Birmingham'
    WHEN evaluation_id ILIKE '%MAI%' THEN 'Maidstone'
    WHEN evaluation_id ILIKE '%TRA%' THEN 'Trafford'
    WHEN evaluation_id ILIKE '%YOR%' THEN 'York'
  END AS council,
  COUNT(DISTINCT source_id) AS total_transcriptions
FROM analytics_event
WHERE event_type = 'TRANSCRIPTION_RECEIVED'
  AND source_id IS NOT NULL
  AND evaluation_id ~* '(HAR|BIR|MAI|TRA|YOR)'
GROUP BY council
ORDER BY council;
"""

## 2. Template Summaries Breakdown (Accurate labeling + Privacy safe)
QUERY_SUMMARIES = """
SELECT
  CASE
    WHEN ae.evaluation_id ILIKE '%HAR%' THEN 'Hart'
    WHEN ae.evaluation_id ILIKE '%BIR%' THEN 'Birmingham'
    WHEN ae.evaluation_id ILIKE '%MAI%' THEN 'Maidstone'
    WHEN ae.evaluation_id ILIKE '%TRA%' THEN 'Trafford'
    WHEN ae.evaluation_id ILIKE '%YOR%' THEN 'York'
  END AS council,
  CASE
    -- User-created/custom template. The event carries an immutable snapshot of the
    -- template id, so these stay classified here even after the template is deleted.
    -- We never surface the name itself, which is user-authored content.
    WHEN ae.event_metadata ->> 'template_id' IS NOT NULL
      THEN 'Custom Template'
    -- Known ready-made template from system:
    WHEN m.template_name IS NOT NULL
      THEN m.template_name
    -- The summary itself is gone: data retention deletes transcriptions (cascading to
    -- minute/minute_version) after each user's data_retention_days, while analytics
    -- events are kept for 12 months. The event survives; the record naming the template
    -- does not. The template is fine -- we just can no longer tell which one was used.
    ELSE 'Summary deleted (template unknown)'
  END AS template,
  COUNT(DISTINCT ae.source_id) AS summaries
FROM analytics_event ae
LEFT JOIN minute_version mv ON mv.id = ae.source_id
LEFT JOIN minute m ON m.id = mv.minute_id
WHERE ae.event_type = 'SUMMARY_RECEIVED'
  AND ae.source_id IS NOT NULL
  AND ae.evaluation_id ~* '(HAR|BIR|MAI|TRA|YOR)'
GROUP BY council, template
ORDER BY council, summaries DESC;
"""

# 3. User Adoption and TOU Acceptance
QUERY_USERS = """
SELECT
  CASE
    WHEN council_code = 'BIR' THEN 'Birmingham'
    WHEN council_code = 'HAR' THEN 'Hart'
    WHEN council_code = 'YOR' THEN 'York'
    WHEN council_code = 'MAI' THEN 'Maidstone'
    WHEN council_code = 'TRA' THEN 'Trafford'
    ELSE council_code
  END AS council,
  total_users,
  accepted_terms
FROM (
  SELECT
    council_code,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (WHERE accepted_tou) AS accepted_terms
  FROM (
    SELECT
      accepted_tou,
      CASE
        WHEN u.evaluation_id ILIKE '%BIR%' THEN 'BIR'
        WHEN u.evaluation_id ILIKE '%HAR%' THEN 'HAR'
        WHEN u.evaluation_id ILIKE '%YOR%' THEN 'YOR'
        WHEN u.evaluation_id ILIKE '%MAI%' THEN 'MAI'
        WHEN u.evaluation_id ILIKE '%TRA%' THEN 'TRA'
      END AS council_code
    FROM "user" u
  ) AS inner_users
  WHERE council_code IS NOT NULL
  GROUP BY council_code
) AS outer_users
ORDER BY council;
"""

# --- Chart Builders (shared by the Streamlit UI and the HTML report) ---

# Pink tooltip, applied to every figure so hovers look the same everywhere
HOVERLABEL = dict(
    bgcolor="#ec4899",        # Pink tooltip background
    font_size=12,
    font_color="#ffffff",     # White text
    bordercolor="#db2777"     # Darker pink border
)

def build_users_figure(df_users):
    # Melt dataframe to make it easy to plot grouped/unstacked bars
    df_melted = df_users.melt(
        id_vars=["council"],
        value_vars=["total_users", "accepted_terms"],
        var_name="Status",
        value_name="Count"
    )
    # Rename for cleaner legend
    df_melted["Status"] = df_melted["Status"].map({
        "total_users": "Total Registered",
        "accepted_terms": "Accepted Terms of Use"
    })

    # Grey = everyone registered, blue = the subset who accepted the terms
    fig = px.bar(
        df_melted,
        x="council",
        y="Count",
        color="Status",
        barmode="group",
        color_discrete_map={"Total Registered": "#94a3b8", "Accepted Terms of Use": "#2563eb"},
        title="User Onboarding by Council",
        text="Count"
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        margin=dict(l=50, r=20, t=80, b=20),
        height=350,
        hoverlabel=HOVERLABEL,
        xaxis_title=None,
        yaxis_title=None,
        # Legend above the plot so it never sits on top of the bars
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text=""
        )
    )
    return fig


def build_transcripts_figure(df_transcriptions):
    fig = px.bar(
        df_transcriptions,
        x="council",
        y="total_transcriptions",
        title="Transcriptions by Council",
        color_discrete_sequence=["#2563eb"],
        text="total_transcriptions"
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        margin=dict(l=50, r=20, t=80, b=20),
        height=350,
        hoverlabel=HOVERLABEL,
        xaxis_title=None,
        yaxis_title=None
    )
    return fig


# --- Table Builders (shared by the Streamlit UI and the HTML report) ---

def format_users_table(df_users):
    """Readable headers, plus an acceptance rate per council."""
    df = df_users.copy()
    df["acceptance_rate"] = [
        f"{(accepted / total * 100):.1f}%" if total else "—"
        for total, accepted in zip(df["total_users"], df["accepted_terms"])
    ]
    return df.rename(columns={
        "council": "Council",
        "total_users": "Invited Users",
        "accepted_terms": "Accepted Terms of Use",
        "acceptance_rate": "% Accepted",
    })


def format_summaries_table(df_summaries):
    return df_summaries.rename(columns={
        "council": "Council",
        "template": "Template",
        "summaries": "Summaries",
    })


# Shown under the template table in both the dashboard and the exported report, so
# readers do not mistake the fallback bucket for a data-quality problem.
TEMPLATE_NOTE = (
    "“Custom Template” covers user-authored templates, whose names are deliberately not shown. "
    "“Summary deleted (template unknown)” means the summary has since been removed by data "
    "retention, so the template it used is no longer recoverable — expect this bucket to grow "
    "with the age of the reporting window."
)


def generate_html_report(df_users, df_transcriptions, df_summaries):
    # include_plotlyjs=True embeds the JS directly inside the file (no external CDN needed)
    chart_users_html = build_users_figure(df_users).to_html(
        full_html=False, include_plotlyjs=True
    )
    # Second chart does not need the JS engine re-embedded; it reuses the first one
    chart_transcripts_html = build_transcripts_figure(df_transcriptions).to_html(
        full_html=False, include_plotlyjs=False
    )

    # 3. KPI numbers
    total_u = int(df_users['total_users'].sum())
    total_tou = int(df_users['accepted_terms'].sum())
    tou_rate = f"{(total_tou/total_u*100):.1f}%" if total_u else "0%"
    total_t = int(df_transcriptions['total_transcriptions'].sum())
    total_s = int(df_summaries['summaries'].sum())

    # 4. Standalone HTML with 100% Inline CSS (No CDN dependencies)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Local Transcribe Insights Report</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #f8fafc;
                color: #1e293b;
                margin: 0;
                padding: 30px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
            .header h1 {{ margin: 0; font-size: 26px; color: #0f172a; display: flex; align-items: center; gap: 12px; }}
            .header p {{ margin: 4px 0 0 0; color: #64748b; font-size: 14px; }}
            
            /* KPI Cards */
            .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
            .card {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 18px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            }}
            .card-title {{ font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; }}
            .card-value {{ font-size: 24px; font-weight: 800; color: #0f172a; margin: 6px 0 0 0; }}
            .card-sub {{ font-size: 12px; font-weight: normal; color: #64748b; }}
            
            /* Layout Grids */
            .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
            
            /* Tables */
            .table-container {{ overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 13px; text-align: left; }}
            th {{ background-color: #f1f5f9; color: #475569; font-weight: 600; padding: 10px 12px; border-bottom: 2px solid #cbd5e1; }}
            td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; color: #334155; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
            tr:last-child td {{ border-bottom: 2px solid #94a3b8; }}
            tr:hover {{ background-color: #f1f5f9; }}
            
            h2 {{ font-size: 16px; font-weight: 700; margin: 0 0 14px 0; color: #1e293b; }}
        </style>
    </head>
    <body>
        <div class="container">
            
            <div class="header">
                <h1>{mhclg_logo_svg(36, 34)}<span>Local Transcribe Quick Insights Report</span></h1>
                <p>Generated: {time.strftime('%d %B %Y, %H:%M')}</p>
            </div>

            <!-- KPIs -->
            <div class="grid-4">
                <div class="card">
                    <p class="card-title">Invited Users</p>
                    <p class="card-value">{total_u}</p>
                </div>
                <div class="card">
                    <p class="card-title">Accepted Terms of Use</p>
                    <p class="card-value" style="color: #2563eb;">{total_tou} <span class="card-sub">({tou_rate})</span></p>
                </div>
                <div class="card">
                    <p class="card-title">Transcriptions</p>
                    <p class="card-value">{total_t}</p>
                </div>
                <div class="card">
                    <p class="card-title">Summaries Produced</p>
                    <p class="card-value">{total_s}</p>
                </div>
            </div>

            <!-- Interactive Plotly Charts -->
            <div class="grid-2">
                <div class="card">
                    {chart_users_html}
                </div>
                <div class="card">
                    {chart_transcripts_html}
                </div>
            </div>

            <!-- Clean Tables -->
            <div class="grid-2">
                <div class="card">
                    <h2>👥 User Onboarding Details</h2>
                    <div class="table-container">
                        {format_users_table(df_users).to_html(index=False, classes="report-table")}
                    </div>
                </div>
                <div class="card">
                    <h2>📝 Summary Breakdown by Template</h2>
                    <div class="table-container">
                        {format_summaries_table(df_summaries).to_html(index=False, classes="report-table")}
                    </div>
                    <p class="card-sub" style="margin: 12px 0 0 0;">{TEMPLATE_NOTE}</p>
                </div>
            </div>
            
        </div>
    </body>
    </html>
    """
    return html_content

# --- Pipeline Execution ---
def run_pipeline():
    ensure_rds_cert()

    env_vars = os.environ.copy()
    env_vars["AWS_PROFILE"] = AWS_PROFILE_NAME
    env_vars["AWS_DEFAULT_REGION"] = REGION

    try:
        subprocess.check_output(
            ["aws", "sts", "get-caller-identity"],
            env=env_vars,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            f"Your AWS SSO session has expired. Please run this in your terminal:\n\n"
            f"aws sso login --profile {AWS_PROFILE_NAME}"
        )

    cmd_tunnel = [SCRIPT_PATH, "--environment", ENV, "--local-port", PORT, "--tunnel-only"]
    tunnel_proc = subprocess.Popen(
        cmd_tunnel, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        env=env_vars
    )
    
    time.sleep(5)

    try:
        db_id = f"{ENV}-database"
        db_host = subprocess.check_output([
            "aws", "rds", "describe-db-instances",
            "--region", REGION,
            "--db-instance-identifier", db_id,
            "--query", "DBInstances[0].Endpoint.Address",
            "--output", "text"
        ], env=env_vars).decode('utf-8').strip()

        db_auth_token = subprocess.check_output([
            "aws", "rds", "generate-db-auth-token",
            "--region", REGION,
            "--hostname", db_host,
            "--port", "5432",
            "--username", "postgres"
        ], env=env_vars).decode('utf-8').strip()

        conn = psycopg2.connect(
            host="127.0.0.1",
            port=PORT,
            dbname="postgres",
            user="postgres",
            password=db_auth_token,
            sslmode="require",
            sslrootcert=CA_PATH
        )

        df_transcriptions = pd.read_sql(QUERY_TRANSCRIPTIONS, conn)
        df_summaries = pd.read_sql(QUERY_SUMMARIES, conn)
        df_users = pd.read_sql(QUERY_USERS, conn)
        conn.close()

        return df_transcriptions, df_summaries, df_users

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise RuntimeError(f"AWS Error: {error_msg}")

    finally:
        tunnel_proc.terminate()
        tunnel_proc.kill()


# --- UI Layout ---
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:14px; margin-bottom:0.25rem;">
        {mhclg_logo_svg(46, 43)}
        <h1 style="margin:0; padding:0; font-size:2.25rem; font-weight:700; line-height:1.2;">
            Local Transcribe Quick Insights Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption(f"Profile: **{AWS_PROFILE_NAME}** | Environment: **{ENV}**")

# Place the Fetch button and the Export button side-by-side
col_btn1, col_btn2, _ = st.columns([1.5, 2.5, 4])

with col_btn1:
    fetch_clicked = st.button("🚀 Fetch Latest Data", type="primary")

with col_btn2:
    if 'data' in st.session_state:
        df_transcriptions, df_summaries, df_users = st.session_state['data']
        
        # Build the HTML report
        html_report = generate_html_report(df_users, df_transcriptions, df_summaries)
        
        st.download_button(
            label="🌐 Download Slack Report (.html)",
            data=html_report,
            file_name=f"local_transcribe_insights_{time.strftime('%Y%m%d')}.html",
            mime="text/html"
        )


if fetch_clicked:
    with st.spinner("Connecting through SSM tunnel & querying database..."):
        try:
            df_transcriptions, df_summaries, df_users = run_pipeline()
            st.session_state['data'] = (df_transcriptions, df_summaries, df_users)
            st.success("Data successfully refreshed!")
            st.rerun()
        except Exception as e:
            st.error(f"Extraction failed: {e}")

# Render Dashboard
if 'data' in st.session_state:
    df_transcriptions, df_summaries, df_users = st.session_state['data']

    st.divider()

    # --- Top Metrics Row ---
    col1, col2, col3, col4 = st.columns(4)
    total_users = int(df_users['total_users'].sum())
    total_tou = int(df_users['accepted_terms'].sum())
    total_transcripts = int(df_transcriptions['total_transcriptions'].sum())
    total_summaries = int(df_summaries['summaries'].sum())

    col1.metric("Invited Users", total_users)
    col2.metric("Accepted Terms of Use", total_tou, f"{(total_tou/total_users*100):.1f}% rate" if total_users else "0%")
    col3.metric("Transcripts Generated", total_transcripts)
    col4.metric("Summaries Produced", total_summaries)

    st.divider()

    # --- Charts Row ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.plotly_chart(build_users_figure(df_users), key="chart_users")

    with chart_col2:
        st.plotly_chart(build_transcripts_figure(df_transcriptions), key="chart_transcripts")

    st.divider()

    # --- Detail Tables Row ---
    table_col1, table_col2 = st.columns(2)

    with table_col1:
        st.subheader("👥 User Onboarding Details")
        st.dataframe(format_users_table(df_users), hide_index=True)

    with table_col2:
        st.subheader("📝 Summary Breakdown by Template")
        st.dataframe(format_summaries_table(df_summaries), hide_index=True)
        st.caption(TEMPLATE_NOTE)