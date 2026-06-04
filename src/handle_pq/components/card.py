

def make_kpi_card(title, value, subtext=""):
    return f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtext}</div>
        </div>
    """