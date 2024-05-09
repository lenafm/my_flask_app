import pandas as pd
import plotly.graph_objects as go
import json
import plotly

def create_demographic_plot(df, region):
    # Assuming the last six columns are demographic categories
    demographic_columns = df.columns[-6:]
    fig = go.Figure()

    for col in demographic_columns:
        value = df.loc[df['region'] == region, col].values[0]
        complement = 100 - value  # Assuming the data are percentages

        fig.add_trace(go.Bar(
            y=[col + ' (%)', 'Non-' + col + ' (%)'],  # Label adjustments if needed
            x=[value, -complement],
            name=col,
            orientation='h',
            text=[f"{value}%", f"{complement}%"],
            textposition='auto'
        ))

    fig.update_layout(
        title=f'Demographic Profiles for {region}',
        xaxis=dict(title='Percentage', range=[-100, 100]),
        yaxis=dict(title='Category'),
        barmode='overlay'
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
