import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


@st.cache_resource
def load_world_map():
    return gpd.read_file('ne_110m_admin_0_countries_lakes/ne_110m_admin_0_countries_lakes.shp')[
        ['ADM0_A3', 'geometry']].to_crs('+proj=robin')


@st.cache_data
def load_raw_data():
    countries = pd.read_csv(
        'https://docs.google.com/spreadsheets/d/e/2PACX-1vSgcOEGH5nEzRQ6zFdiDxB0S3xHtZ8BUR039zmtnw5hj7mfycCHrdIr2hcc_WM4uR_NNS0z7Bg2ho_c/pub?gid=0&single=true&output=csv',
        usecols=['alpha_3', 'stage', 'reboot', 'subEntities'], na_filter=False)

    stages = pd.read_csv(
        'https://docs.google.com/spreadsheets/d/e/2PACX-1vSgcOEGH5nEzRQ6zFdiDxB0S3xHtZ8BUR039zmtnw5hj7mfycCHrdIr2hcc_WM4uR_NNS0z7Bg2ho_c/pub?gid=1702276270&single=true&output=csv',
        usecols=['code', 'label_fr', 'label_en', 'baseColor', 'stripeColor'], na_filter=False)
    stages = stages[stages.code != ""]

    return countries, stages


@st.cache_data
def prepare_legend(legend, lang):
    legend['label'] = legend['label_fr'] if lang == 'FR' else legend['label_en']
    return legend


@st.cache_data
def prepare_data(_shapefile, raw_data):
    # Merge countries with stages
    data = raw_data.merge(legend, left_on='stage', right_on='code', how='left')
    data = data.drop('code', axis=1)

    # Merge the map with the countries DataFrame
    data = _shapefile.merge(data, left_on='ADM0_A3', right_on="alpha_3", how='left')

    # Default color for other countries
    data['baseColor'].fillna('lightgrey', inplace=True)
    data.loc[pd.isna(data['stripeColor']), 'stripeColor'] = ''
    data['stripe'] = data['stripeColor'] != ''
    data.loc[data['stripeColor'] == '', 'stripeColor'] = '#00000000'
    data = data[data.ADM0_A3 != 'ATA'].reset_index(drop=True)

    return data


@st.cache_resource
def make_plot(_data, legend, lang):
    # _ needed for cache
    data = _data

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(28, 14))

    # # Iterate through the DataFrame and plot each country
    for feature in data.iterfeatures():

        # Extract attributes
        idx = feature['id']
        geom = feature['geometry']
        properties = feature['properties']
        baseColor = properties['baseColor']
        stripeColor = properties['stripeColor']
        stripe = properties['stripe']
        reboot = properties['reboot']
        subEntities = properties['subEntities']
        if stripe:
            data.iloc[[idx]].plot(ax=ax, facecolor=baseColor, edgecolor=stripeColor, hatch='//')
        else:
            data.iloc[[idx]].plot(ax=ax, color=baseColor, edgecolor='black')
        if reboot:
            data.iloc[[idx]].plot(ax=ax, facecolor=baseColor, edgecolor='black', hatch='|')
        if subEntities:
            data.iloc[[idx]].plot(ax=ax, facecolor=baseColor, edgecolor='black', hatch='.')

    date = datetime.now().strftime("%d %b %Y")
    if lang == 'FR':
        title = f"Carte Historionomique Mondiale - {date}"
    else:
        title = f"Historionomic World Map - {date}"

    ax.set_title(title, fontsize=30, color='black')
    ax.set_axis_off()

    # Create a list of patches for the legend
    patches = [
        mpatches.Patch(facecolor=l.baseColor, edgecolor=l.stripeColor, hatch='///',
                       label=l.label) if l.stripeColor != '' else
        mpatches.Patch(color=l.baseColor, label=l.label)
        for l in legend.itertuples()]
    patches.append(mpatches.Patch(facecolor='white', edgecolor='black', hatch='||', label='Reboot'))
    patches.append(mpatches.Patch(facecolor='white', edgecolor='black', hatch='..',
                                  label='Sous-entités hétérogènes' if lang == 'FR' else 'Heterogeneous sub-entities'))

    # Add the legend to the plot
    l = ax.legend(handles=patches[2:], loc='lower left', fontsize=14, title_fontsize='large', edgecolor='black')
    l.get_frame().set_alpha(0.9)

    plt.tight_layout()

    return plt


# Main code

lang = st.selectbox('Language', ['FR', 'EN'])

shapefile = load_world_map()
raw_data, raw_legend = load_raw_data()

legend = prepare_legend(raw_legend, lang)
data = prepare_data(shapefile, raw_data)

plot = make_plot(data, legend, lang)

st.pyplot(plot)
