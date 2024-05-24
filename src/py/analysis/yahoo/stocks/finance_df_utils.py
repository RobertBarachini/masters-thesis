import os
from re import sub
from datetime import datetime
import pandas as pd
from plotly import subplots
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

# Globals
default_window = 20  # 20 samples


def load_stock_csv(path: str) -> pd.DataFrame:
	'''
		Load stock data from csv file

		Can be used to load data from Yahoo Finance (stocks, crypto, ...)
	'''
	df = pd.read_csv(path)
	# Convert Date to datetime and set as index
	df["Date"] = pd.to_datetime(df["Date"])  # type: ignore
	df = df.set_index("Date")
	# Set Open, High, Low, Close, Adj Close to float and Volume to int
	df[["Open", "High", "Low", "Close",
	    "Adj Close"]] = df[["Open", "High", "Low", "Close",
	                        "Adj Close"]].astype(float)  # type: ignore
	df["Volume"] = df["Volume"].astype(int)
	return df


def filter_df_by_date(df: pd.DataFrame,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> pd.DataFrame:
	'''
		Filter DataFrame by start and end date
	'''
	if start_date is not None:
		df = df[df.index >= start_date]
	if end_date is not None:
		df = df[df.index <= end_date]
	return df


def assert_window(window: int, df_len: int) -> None:
	if window < 1:
		raise Exception(f"Window must be greater than 0")
	if window > df_len:
		raise Exception(f"Window must be less than length of DataFrame")


def get_sma(df: pd.DataFrame, window: int, column_name: str) -> pd.Series:
	'''
		Get Simple Moving Average (SMA) for DataFrame (default column: Close)
	'''
	return df[column_name].rolling(window=window).mean()


def get_std(df: pd.DataFrame, window: int, column_name: str) -> pd.Series:
	'''
		Get Standard Deviation for DataFrame
	'''
	return df[column_name].rolling(window=window).std()


def get_ema(df: pd.DataFrame, window: int, column_name: str) -> pd.Series:
	'''
		Get Exponential Moving Average (EMA) for DataFrame
	'''
	return df[column_name].ewm(span=window).mean()


def get_rsi(df: pd.DataFrame,
            window: Optional[int] = 14,
            column_name: Optional[str] = "Close") -> pd.Series:
	'''
		Get Relative Strength Index (RSI) for DataFrame
	'''
	if column_name not in df.columns:
		raise Exception(f"Column {column_name} not in DataFrame")
	if window is None:
		window = default_window
	assert_window(window, len(df))
	if column_name is None:
		column_name = "Close"
	# Get difference between current and previous close
	df["RSI_diff"] = df[column_name].diff()
	# Get positive and negative values
	df["RSI_pos"] = df["RSI_diff"].apply(lambda x: x if x > 0 else 0)
	df["RSI_neg"] = df["RSI_diff"].apply(lambda x: x if x < 0 else 0)
	# Get average gain and average loss
	df["RSI_avg_gain"] = df["RSI_pos"].rolling(window=window).mean()
	df["RSI_avg_loss"] = df["RSI_neg"].rolling(window=window).mean()
	# Calculate RSI
	df["RSI"] = 100 - (100 / (1 + (df["RSI_avg_gain"] / df["RSI_avg_loss"])))
	# # Drop columns
	# df = df.drop(columns=[
	#     "RSI_diff", "RSI_pos", "RSI_neg", "RSI_avg_gain", "RSI_avg_loss"
	# ])
	return df["RSI"]


def calculate_series(series_name: str,
                     df: pd.DataFrame,
                     window: Optional[int] = default_window,
                     column_name: Optional[str] = "Close") -> pd.Series:
	'''
		Calculate series for DataFrame
	'''
	if column_name not in df.columns:
		raise Exception(f"Column {column_name} not in DataFrame")
	if window is None:
		window = default_window
	assert_window(window, len(df))
	if column_name is None:
		column_name = "Close"
	if series_name == "SMA":
		return get_sma(df, window, column_name)
	elif series_name == "STD":
		return get_std(df, window, column_name)
	elif series_name == "EMA":
		return get_ema(df, window, column_name)
	elif series_name == "RSI":
		return get_rsi(df, window=window, column_name=column_name)
	else:
		raise Exception(f"Series {series_name} not implemented")


def df_add_data(df: pd.DataFrame,
                options: Optional[dict] = None) -> pd.DataFrame:
	'''
		Adds specific columns to DataFrame
	'''
	if options is None:
		options = {
		    "Window": default_window,  # window for SMA, Bollinger Bands, ...
		    "SMA": True,  # Simple Moving Average
		    "SMA_volume": True,  # Simple Moving Average for Volume
		    "Bollinger": True,  # Bollinger Bands
		    "EMA": True,  # Exponential Moving Average
		    "RSI": True,  # Relative Strength Index
		    "MACD": True,  # Moving Average Convergence Divergence
		    "Close diff %": [
		        1, 7, 30, 365
		    ],  # daily, weekly, monthly, yearly difference in percent (close)
		    "Volume diff %": [1, 7, 30, 365]
		}
	# Add window
	if "Window" not in options:
		options["Window"] = default_window
	df["Window"] = options["Window"]
	# Prepare
	std = -1
	# Add SMA
	if options["SMA"]:
		df["SMA"] = calculate_series("SMA",
		                             df,
		                             window=options["Window"],
		                             column_name="Close")
	# Add SMA Volume
	if options["SMA_volume"]:
		df["SMA_volume"] = calculate_series("SMA",
		                                    df,
		                                    window=options["Window"],
		                                    column_name="Volume")
	# Add Bollinger Bands
	if options["Bollinger"]:
		if std == -1:
			std = calculate_series("STD",
			                       df,
			                       window=options["Window"],
			                       column_name="Close")
		df["BB Upper"] = df["SMA"] + (2 * std)
		df["BB Lower"] = df["SMA"] - (2 * std)
	# Add EMA
	if options["EMA"]:
		df["EMA"] = calculate_series("EMA",
		                             df,
		                             window=options["Window"],
		                             column_name="Close")
	# Add RSI
	if options["RSI"]:
		df["RSI"] = calculate_series("RSI",
		                             df,
		                             window=options["Window"],
		                             column_name="Close")
	# Add MACD
	if options["MACD"]:
		df["EMA_12"] = calculate_series("EMA", df, window=12, column_name="Close")
		df["EMA_26"] = calculate_series("EMA", df, window=26, column_name="Close")
		df["MACD"] = df["EMA_12"] - df["EMA_26"]
		df["MACD_signal"] = calculate_series("EMA",
		                                     df,
		                                     window=9,
		                                     column_name="MACD")
		df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
		df["MACD_hist_SMA"] = calculate_series("SMA",
		                                       df,
		                                       window=options["Window"],
		                                       column_name="MACD_hist")

	# # Shift SMA and Bollinger Bands by window
	# df["SMA"] = df["SMA"].shift(int(options["Window"] / 2) * -1)
	# df["BB Upper"] = df["BB Upper"].shift(int(options["Window"] / 2) * -1)
	# df["BB Lower"] = df["BB Lower"].shift(int(options["Window"] / 2) * -1)
	# # Shift EMA by window
	# df["EMA"] = df["EMA"].shift(int(options["Window"] / 2) * -1)

	# TODO: fix this
	# # Add Close diff %
	# if "Close diff %" in options:
	# 	for days in options["Close diff %"]:
	# 		df[f"Close diff % {days}"] = df["Close"].pct_change(periods=days)
	# # Add Volume diff %
	# if "Volume diff %" in options:
	# 	for days in options["Volume diff %"]:
	# 		df[f"Volume diff % {days}"] = df["Volume"].pct_change(periods=days)
	return df


# TODO: use options to turn on/off certain series (like MACD)
def get_figure(df: pd.DataFrame,
               title: str,
               options: Optional[dict] = None) -> go.Figure:
	'''
		Get figure for DataFrame with added data
	'''
	# Local variables
	increasing_color = '#428561'
	decreasing_color = '#D53C36'
	# default_color = # plotly default color
	default_color = px.colors.qualitative.Plotly[0]

	# Check options
	if options is None:
		options = {}
	if "w" not in options:
		options["w"] = 1920
	if "h" not in options:
		options["h"] = 1080
	if "traces" not in options:
		options["traces"] = ["Candlestick", "SMA", "BB", "EMA", "RSI", "Volume"]
	for i in range(len(options["traces"])):
		options["traces"][i] = options["traces"][i].lower()
	if "margin" not in options:
		options["margin"] = None
	if "labels" not in options:
		options["labels"] = None
	if "color_changes" not in options:  # whether to color changes in candlestick chart
		options["color_changes"] = True

	if options["color_changes"] == False:
		increasing_color = default_color
		decreasing_color = default_color

	# Create figure
	fig = subplots.make_subplots(rows=3,
	                             cols=1,
	                             shared_xaxes=True,
	                             vertical_spacing=0.01,
	                             row_heights=[0.6, 0.2, 0.2])

	# Add candlestick chart
	trace_candlestick = go.Candlestick(
	    x=df.index,
	    open=df["Open"],
	    high=df["High"],
	    low=df["Low"],
	    close=df["Close"],
	    name="Candlestick",
	)

	# Add SMA line
	trace_sma = go.Scatter(
	    x=df.index,
	    y=df["SMA"],
	    name="SMA",
	    line={
	        "color": "rgba(0,0,0,0.5)",
	    },
	    opacity=0.3,
	)

	# Add Bollinger Bands
	trace_bb_upper = go.Scatter(
	    x=df.index,
	    y=df["BB Upper"],
	    name="BB Upper",
	    mode="lines",
	    line={
	        "dash": "dash",
	        "color": "rgba(0,0,0,0.5)",
	    },
	    opacity=0.3,
	)
	trace_bb_lower = go.Scatter(
	    x=df.index,
	    y=df["BB Lower"],
	    name="BB Lower",
	    mode="lines",
	    line={
	        "dash": "dash",
	        "color": "rgba(0,0,0,0.5)",
	    },
	    fill="tonexty",
	    fillcolor="rgba(0,0,0,0.125)",
	    opacity=0.3,
	)

	# Add EMA line
	trace_ema = go.Scatter(
	    x=df.index,
	    y=df["EMA"],
	    name="EMA",
	    # orange color
	    line={
	        "color": "rgba(255, 127, 14, 1)",
	    },
	    opacity=0.8,
	    # line={
	    #     "color": "rgba(0,0,0,0.5)",
	    # },
	    # opacity=0.3,
	)

	# Add RSI line
	trace_rsi = go.Scatter(
	    x=df.index,
	    y=df["RSI"],
	    name="RSI",
	    # purple color
	    line={
	        "color": "rgba(148, 103, 189, 1)",
	    },
	    opacity=0.8,
	)

	# Add volume bar chart
	volume_colors = [
	    increasing_color if close > open else decreasing_color
	    for open, close in zip(df["Open"], df["Close"])
	]
	trace_volume = go.Bar(x=df.index,
	                      y=df["Volume"],
	                      name="Volume",
	                      marker={"color": volume_colors},
	                      opacity=1)

	# Add SMA Volume line
	trace_sma_volume = go.Scatter(
	    x=df.index,
	    y=df["SMA_volume"],
	    name="Volume SMA",
	    line={
	        "color": "rgba(0,0,0,0.5)",
	    },
	    opacity=0.5,
	)

	# # Add MACD line
	# trace_macd = go.Scatter(
	#     x=df.index,
	#     y=df["MACD"],
	#     name="MACD",
	#     # green color
	#     line={
	#         "color": "rgba(44, 160, 44, 1)",
	#     },
	#     opacity=0.8,
	# )

	# # Add MACD signal line
	# trace_macd_signal = go.Scatter(
	#     x=df.index,
	#     y=df["MACD_signal"],
	#     name="MACD signal",
	#     # purple color, dashed
	#     line={
	#         "color": "rgba(148, 103, 189, 1)",
	#         # "dash": "dash",
	#     },
	#     opacity=0.8,
	# )

	# Add MACD histogram
	histogram_colors = [
	    increasing_color if hist > 0 else decreasing_color
	    for hist in df["MACD_hist"]
	]
	trace_macd_hist = go.Bar(
	    x=df.index,
	    y=df["MACD_hist"],
	    name="MACD",  # name="MACD histogram",
	    marker={"color": volume_colors},
	    opacity=1)
	# Add SMA MACD histogram line
	trace_macd_hist_sma = go.Scatter(
	    x=df.index,
	    y=df["MACD_hist_SMA"],
	    name="MACD SMA",  # name="MACD histogram SMA",
	    line={
	        "color": "rgba(0,0,0,0.5)",
	    },
	    opacity=0.5,
	)

	# Arrange all elements
	# First row
	if "candlestick" in options["traces"]:
		fig.add_trace(trace_candlestick, row=1, col=1)
	fig.add_trace(trace_sma, row=1, col=1)
	fig.add_trace(trace_bb_upper, row=1, col=1)
	fig.add_trace(trace_bb_lower, row=1, col=1)
	fig.add_trace(trace_ema, row=1, col=1)
	# fig.add_trace(trace_rsi, row=1, col=1) # this is broken - fix it, also check others
	# Second row
	fig.add_trace(trace_volume, row=2, col=1)
	fig.add_trace(trace_sma_volume, row=2, col=1)
	# Third row
	# fig.add_trace(trace_macd, row=3, col=1)
	# fig.add_trace(trace_macd_signal, row=3, col=1)
	fig.add_trace(trace_macd_hist, row=3, col=1)
	fig.add_trace(trace_macd_hist_sma, row=3, col=1)

	# Name axes
	if options["labels"] is None:
		fig.update_yaxes(title_text="Price ($)", row=1, col=1)
		fig.update_yaxes(title_text="Volume", row=2, col=1)
		fig.update_yaxes(title_text="MACD", row=3, col=1)
	else:
		for i, row in enumerate(options["labels"]):
			fig.update_yaxes(title_text=row, row=i + 1, col=1)
	fig.update_xaxes(title_text="Date", row=3, col=1)  # preset

	# Set title
	fig.update_layout(title_text=title)

	# Hide scaling buttons
	fig.update_layout(xaxis=dict(rangeslider=dict(visible=False)))

	# Show legend
	fig.update_layout(showlegend=True)
	# fig.update_layout(legend={"traceorder": "reversed"})

	# Enable xaxes grid
	fig.update_xaxes(showgrid=True)

	# Legend order
	fig.update_layout(legend=dict(traceorder="normal"))

	# Turn off certain traces from being displayed at start, but allow user to turn them on
	# turn off MACD signal and MACD
	# trace_macd.visible = "legendonly" # TODO: this doesn't work - fix this
	# trace_macd_signal.visible = False

	# lower bar spacing
	fig.update_layout(bargap=0)
	# remove bar borders
	fig.update_traces(marker_line_width=0, row=2, col=1)
	fig.update_traces(marker_line_width=0, row=3, col=1)

	# Set size
	fig.update_layout(width=options["w"], height=options["h"])

	# Set margin
	if options["margin"] is not None:
		fig.update_layout(margin=options["margin"])

	# Return figure
	return fig


# def add_vline_annotation(fig: go.Figure,
#                          event: dict,
#                          textangle: float = 0) -> go.Figure:
# 	'''
# 		Add vertical line annotation to figure
# 	'''
# 	if "line_width" not in event:
# 		event["line_width"] = 1
# 	if "color" not in event:
# 		event["color"] = "black"
# 	if "line_dash" not in event:
# 		event["line_dash"] = "dash"  # dash, dot, dashdot
# 	if "annotation" not in event:
# 		raise Exception("Missing annotation")
# 	if "date" not in event:
# 		raise Exception("Missing date")
# 	fig.add_vline(x=event["date"],
# 	              line_width=event["line_width"],
# 	              line_color=event["color"],
# 	              line_dash=event["line_dash"],
# 	              opacity=0.3)
# 	# get height of top plot
# 	y_top = fig.layout.yaxis.domain[1]  # type: ignore
# 	fig.add_annotation(
# 	    x=event["date"],
# 	    y=1.032,
# 	    text=event["annotation"],
# 	    showarrow=False,
# 	    yref="paper",  # "y",
# 	    # set color to same as line
# 	    font={
# 	        "color": event["color"],
# 	        "size": 10,
# 	    },
# 	    # opacity=0.5,
# 	    textangle=textangle,
# 	    yshift=y_top - 25,
# 	    # rotate around left edge,
# 	    xshift=-7,
# 	    xanchor="left",
# 	    yanchor="bottom",
# 	    # align="left",
# 	    # TODO: how to set rotation point to left edge?
# 	)
# 	#  yshift=y_top)
# 	return fig

# def add_vline_annotation(fig: go.Figure,
#                          event: dict,
#                          textangle: float = 0) -> go.Figure:
# 	'''
# 		Add vertical line annotation to figure
# 	'''
# 	if "line_width" not in event:
# 		event["line_width"] = 1
# 	if "color" not in event:
# 		event["color"] = "black"
# 	if "line_dash" not in event:
# 		event["line_dash"] = "dash"  # dash, dot, dashdot
# 	if "annotation" not in event:
# 		raise Exception("Missing annotation")
# 	if "date" not in event:
# 		raise Exception("Missing date")
# 	if "y_shift" not in event:
# 		event["y_shift"] = 20
# 	textangle = -90
# 	opacity = 0.5
# 	fig.add_vline(
# 	    x=event["date"],
# 	    line_width=event["line_width"],
# 	    line_color=event["color"],
# 	    line_dash=event["line_dash"],
# 	    opacity=opacity,
# 	)
# 	# get height of top plot
# 	y_top = fig.layout.yaxis.domain[1]  # type: ignore
# 	fig.add_annotation(
# 	    x=event["date"],
# 	    y=1.032,
# 	    text=f"<b>{event['annotation']}</b>",
# 	    showarrow=False,
# 	    yref="paper",  # "y",
# 	    # set color to same as line
# 	    font={
# 	        "color": event["color"],
# 	        # "color": "black",
# 	        # "color": "#2E3F5F",
# 	        "size": 10,
# 	    },
# 	    # opacity=opacity,
# 	    textangle=textangle,
# 	    yshift=y_top - event["y_shift"],
# 	    # rotate around left edge,
# 	    xshift=3,  # 4,
# 	    xanchor="right",
# 	    yanchor="top",
# 	    # align="left",
# 	    # TODO: how to set rotation point to left edge?
# 	)
# 	#  yshift=y_top)
# 	return fig


# Fine-tuned for specific visualization specs (for this thesis)
def add_vline_annotation(fig: go.Figure,
                         event: dict,
                         textangle: float = 0) -> go.Figure:
	'''
		Add vertical line annotation to figure
	'''
	if "line_width" not in event:
		event["line_width"] = 1
	if "color" not in event:
		event["color"] = "black"
	if "line_dash" not in event:
		event["line_dash"] = "dash"  # dash, dot, dashdot
	if "annotation" not in event:
		raise Exception("Missing annotation")
	if "date" not in event:
		raise Exception("Missing date")

	# Default top slanted, otherwise vertical inside a plot (if offset is set)
	y_top = fig.layout.yaxis.domain[1]  # type: ignore
	opacity = 0.3
	xshift = -7
	yshift = y_top - 25
	textangle = -30
	xanchor = "left"
	yanchor = "bottom"
	if "offset" in event:
		textangle = -90
		xshift = -3
		yshift = y_top - 20
		xanchor = "left"
		yanchor = "top"
	fig.add_vline(
	    x=event["date"],
	    line_width=event["line_width"],
	    line_color=event["color"],
	    line_dash=event["line_dash"],
	    opacity=opacity,
	)

	fig.add_annotation(
	    x=event["date"],
	    y=1.032,
	    text=f"<b>{event['annotation']}</b>",
	    showarrow=False,
	    yref="paper",  # "y",
	    # set color to same as line
	    font={
	        "color": event["color"],
	        # "color": "black",
	        # "color": "#2E3F5F",
	        "size": 10,
	    },
	    # opacity=opacity,
	    opacity=0.8,  #0.8,
	    textangle=textangle,
	    yshift=yshift,
	    # rotate around left edge,
	    xshift=xshift,
	    xanchor=xanchor,
	    yanchor=yanchor,
	    # align="left",
	    # TODO: how to set rotation point to left edge?
	)
	#  yshift=y_top)
	return fig


def get_grouped_df(df: pd.DataFrame,
                   match_column_name: Optional[str] = None,
                   match_value: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> pd.DataFrame:
	"""
		Filter dataframe by match_column_name == match_value, only keep numeric columns, group by date and calculate mean, then add data (like SMA).
	"""
	# Copy dataframe
	df_grouped = df.copy()
	# Filter by match_column_name == match_value
	if match_column_name is not None and match_value is not None:
		df_grouped = df[df[match_column_name] == match_value]
	# Only keep numeric columns
	df_grouped = df_grouped.select_dtypes(include="number")
	# Group by date (index) and calculate mean
	# df_grouped = df_grouped.groupby(df_grouped.index).mean()
	# open, high, low, close, adj close is mean, volume is sum
	df_grouped = df_grouped.resample("D").agg({
	    "Open": "mean",
	    "High": "mean",
	    "Low": "mean",
	    "Close": "mean",
	    "Adj Close": "mean",
	    "Volume": "sum"
	})
	# Drop rows with resampled data with NaN
	df_grouped = df_grouped.dropna()
	# Add data
	df_grouped = df_add_data(df_grouped)  # type: ignore
	# Filter by date
	if start_date is not None:
		df_grouped = df_grouped[df_grouped.index >= start_date]
	if end_date is not None:
		df_grouped = df_grouped[df_grouped.index <= end_date]
	return df_grouped


def get_safe_filename(filename: str) -> str:
	'''
		Make filename safe for saving
	'''
	filename_safe = filename.replace(" ", "-").replace("/", "-").replace(
	    "'", "-").replace(",", "-").replace("(", "-").replace(")", "-")
	# replace consecutive dashes with single dash
	filename_safe = sub(r"-+", "-", filename_safe)
	return filename_safe


def save_fig(fig: go.Figure, path: str, scale: float = 1) -> None:
	'''
		Save a figure as a png file.
	'''
	fig.write_image(path, scale=scale)


if __name__ == "__main__":
	# Load data
	df = load_stock_csv("data/scraped/yahoo/stocks/csv/MSFT.csv")
	# print(f"Size in memory (base df): {df.memory_usage().sum() / 1024**2} MB")
	# Filter after 2018-10-01 (leave some for SMA)
	df = filter_df_by_date(df, start_date="2018-10-01")
	# Add data
	df = df_add_data(df)
	# print(df.head())
	# print(df.tail())
	# print(df.dtypes)
	# Print size in memory (MB)
	# print(
	#     f"Size in memory (df with added data): {df.memory_usage().sum() / 1024**2} MB"
	# )
	# Filter after 2019-01-01
	df = filter_df_by_date(df, start_date="2019-01-01")
	# Get figure
	fig = get_figure(df, "Microsoft")
	# Add annotation
	event_covid_crash = {
	    "date": datetime(2020, 2, 20),
	    "annotation": "COVID-19 market crash"
	}
	add_vline_annotation(fig, event_covid_crash)
	event_covid_crash_end = {
	    "date": datetime(2020, 4, 7),
	    "annotation": "COVID-19 market crash end"
	}
	add_vline_annotation(fig, event_covid_crash_end)
	fig.show()
	print("Done!")
