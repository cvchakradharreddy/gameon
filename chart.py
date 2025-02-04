import streamlit as st
import pandas as pd
import altair as alt
import datetime
import numpy as np

def draw_chart(df_chart, video_total_time=24):
    # Convert time to seconds for the chart
    df_chart["Time (seconds)"] = df_chart["Time"].apply(lambda x: sum(int(t) * 60 ** i for i, t in enumerate(reversed(x.split(':')))))

    # 1. Create dummy data points at the start and end of the video:
    if not df_chart["Time (seconds)"].empty: # Check if there are any time points
        min_time = df_chart["Time (seconds)"].min()
        max_time = df_chart["Time (seconds)"].max()

        if min_time > 0:
            df_chart = pd.concat([pd.DataFrame({"Time": "00:00:00", "Event": "Excitement", "Type": "Excitement", "Value": 0, "Time (seconds)": 0}, index=[0]), df_chart], ignore_index=True)

        if max_time < video_total_time:
            df_chart = pd.concat([df_chart, pd.DataFrame({"Time": datetime.timedelta(seconds=video_total_time), "Event": "Excitement", "Type": "Excitement", "Value": 0, "Time (seconds)": video_total_time}, index=[0])], ignore_index=True)

        df_chart = df_chart.sort_values("Time (seconds)") # Sort after adding dummy points
    df_chart['Event'] = df_chart['Event'].astype(str)
    # 2. Create a new DataFrame with interpolated values
    time_range = np.arange(0, video_total_time + 1, 1) # Create a range of seconds with a 1-second interval
    df_interpolated = pd.DataFrame({"Time (seconds)": time_range})

    # Merge with original data and interpolate
    df_interpolated = pd.merge(df_interpolated, df_chart[["Time (seconds)", "Value"]], on="Time (seconds)", how="left")
    df_interpolated["Value"] = df_interpolated["Value"].interpolate(method='linear', limit_direction='both') # Interpolate missing values

    # In the charting section:
    y_max = df_interpolated['Value'].max()
    if y_max > 10:
        y_max = 10  # Ensure y-axis doesn't exceed 10
    # Altair Chart using the INTERPOLATED data
    alt_chart = alt.Chart(df_interpolated).encode(  # Use df_interpolated here
        x=alt.X("Time (seconds)", title="Time", scale=alt.Scale(domain=[0, video_total_time-1])),
        y=alt.Y("Value", title="Excitement", scale=alt.Scale(domain=[0, y_max]))  # Set the y-axis scale
    )
    # Area chart for excitement
    area = alt_chart.mark_area(
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='lightyellow', offset=0),
                alt.GradientStop(color='orange', offset=1)],
            x1=1,
            x2=1,
            y1=1,
            y2=0
        ),
        opacity=0.6,
        interpolate='monotone' # or 'monotone', 'linear', 'basis', 'cardinal' etc. Experiment!
    ).encode(
        x=alt.X("Time (seconds)", title="Time"), #Remove x-axis label
        y=alt.Y("Value", title="Excitement"), # Remove y-axis label
        y2=alt.value(0)
    )

    # Points for Highlights - Overlayed on the area chart
    key_moments_data = df_chart[df_chart["Type"] == "Highlight"]
    if not key_moments_data.empty:
        # Merge key_moments_data with df_interpolated to get the correct y-values
        key_moments_data = pd.merge(key_moments_data, df_interpolated, on="Time (seconds)", how="left")

        points = alt.Chart(key_moments_data).mark_circle(
            color="red", size=100
        ).encode(
            x=alt.X("Time (seconds)", title="Time"),
            y=alt.Y("Value_y", title="Excitement"), # Use the interpolated "Value"
            tooltip=["Event", "Time (seconds)"]  # Use the original "Value" for tooltip
        )

        # Text labels - Positioned above the points
        text = alt.Chart(key_moments_data).mark_text(
            align='center',  # Center the text horizontally
            baseline='middle',  # Vertically align the text to the middle
            dy=-15, # Adjust vertical offset to position above the point (-ve moves it up)
            angle=5,
            color="white" 
        ).encode(
            x=alt.X("Time (seconds)", title="Time"),
            y=alt.Y("Value_y", title="Excitement"),
            text="Event"  # Use the 'label' column for the text
        )

        # Combine area and points using the + operator
        final_chart = area + points # Overlay points on the area

        # Remove gridlines from the FINAL (layered) chart
        final_chart = final_chart.configure_axis(
            grid=False,  # Remove gridlines
            #domain=False,
            ticks=False,
            #labels=False,
            #title=None
        ).properties(
            title="Excitement and Highlights",
            height=200,
        )

        st.altair_chart(final_chart, use_container_width=True) # Display the combined chart
    else: #If there are no Highlights, just display the area chart
      st.altair_chart(area, use_container_width=True)