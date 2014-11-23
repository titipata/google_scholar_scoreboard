# Example code to run scoreboard in IPython Notebook
# %pylab qt4
#
# from gs_board import start_scoreboard, stop_scoreboard, draw_simple_scoreboard
#
# gs_id_list = ['GAi23ssAAAAJ','MiFqJGcAAAAJ', 'JtltLUAAAAAJ', 
#               'tbfWCDgAAAAJ', 'T8W-5LsAAAAJ','jjvixpcAAAAJ', 
#               'wdFV87UAAAAJ', 'AlTQrFcAAAAJ', 'uwpOnSAAAAAJ',
#               'JG7xb2AAAAAJ', 'xxDk3-EAAAAJ', '9jqURCEAAAAJ']
# opts = {'title': 'Bayesian Behavior Lab',
#         'img_link': 'https://raw.githubusercontent.com/titipata/klab_ipython_notebook/master/logo_collection/klab_logo_only.png',
#         'accuweather_link': 'http://www.accuweather.com/en/us/chicago-il/60608/weather-forecast/348308'}
# fig = start_scoreboard(gs_id_list, opts)
# timer = fig.canvas.new_timer(interval=1000*60*0.5)
# timer.add_callback(draw_simple_scoreboard, gs_id_list, opts)
# timer.start()
#
#
# To stop scoreboard run:
# stop_scoreboard(timer)

import time
import pygame
import cStringIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from urllib2 import urlopen
from lxml import etree
from lxml import html
from PIL import Image

def get_scholar_matrix(google_scholar_id):
    ''' function to scarpe scholar matrix given google scholar id
        input: google_scholar_id 
        output: dictionary of '''
    url = 'http://scholar.google.com/citations?user=%s&hl=en&oi=sra' % google_scholar_id
    try:
        tree = html.parse(url)
    except:
        print "No Google Scholar ID found!"
        return None
    cit_table = tree.xpath("//div[@id='gs_top']/div[@id='gsc_bdy']/\
                            div[@id='gsc_rsb']/div[@class='gsc_rsb_s']\
                            /table[@id='gsc_rsb_st']//tr//td[@class='gsc_rsb_std']")
    name = tree.xpath("//div[@class='gsc_lcl']//div[@id='gsc_prf_in']")
    affiliation = tree.xpath("//div[@class='gsc_lcl']//div[@class='gsc_prf_il']")
    if len(name[0].text.split()) > 1:
        first_name = name[0].text.split()[0]
        last_name = name[0].text.split()[-1]
    else:
        first_name = name[0].text # assume first name
        last_name = ""
    scholar_info = {'name': name[0].text,
                    'first_name': first_name,
                    'last_name': last_name,
                    'citation': int(cit_table[0].text),
                    'citation_2009': int(cit_table[1].text),
                    'h_index': int(cit_table[2].text),
                    'i_index': int(cit_table[4].text)
                    }
    return scholar_info


def get_all_scholar_matrix(gs_id_list):
    ''' function to scrape over google scholar id list
        then return dataframe of all google scholar list
    '''
    gs_all = []
    for g_id in gs_id_list:
        scholar_info = get_scholar_matrix(g_id)
        gs_all.append(scholar_info)
    gs_all = pd.DataFrame(gs_all)
    return gs_all


def sort_by_citation(all_people):
    ''' Sort the given dataframe by citation '''
    all_people_sorted = all_people.sort(columns=['h_index', 'citation'],
                                        ascending=False)
    all_people_sorted.index = np.arange(len(all_people))
    return all_people_sorted

def compute_gini(y):
    ''' function to compute Gini index '''
    N = len(y)
    gini = float(2*np.array(sorted(y, reverse=False)).dot(np.arange(1, N+1))
                 /(float(N)*np.sum(y)) - ((N+1.0)/float(N)))
    gini = np.ceil(gini * 1000) / 1000.0
    return gini

def get_difference(gs_old, gs_new):
    ''' return different dataframe from two citation dataframe
    '''
    diff_all = []
    cite_diff = np.array(gs_new.citation - gs_old.citation)
    idx_diff = cite_diff.nonzero()[0]
    name_diff = list(gs_old.first_name[idx_diff])
    for name in name_diff:
        idx = int(np.where(name == gs_old.first_name)[0])
        cit_diff = (gs_new.citation - gs_old.citation)[idx]
        sign_pm = np.int(np.sign(cit_diff))
        if sign_pm == 1:
            sign_pm = '+'
        else:
            sign_pm = '-'
        h_index_diff = (gs_new.h_index - gs_old.h_index)[idx]
        diff_all.append({'name': name, 
                         'cit_diff': cit_diff,
                         'h_index_diff': h_index_diff,
                         'sign': sign_pm})
        diff_all = pd.DataFrame(diff_all)
    return diff_all


def play_music(music_dir):
    ''' Play Everything is Awesome wavfile track '''
    pygame.init()
    pygame.mixer.music.load(music_dir)
    pygame.mixer.music.play()

def get_accuweather_temp(accu_url):
    ''' Function to scrape accuweather from the webpage of the city
    example - 'http://www.accuweather.com/en/us/chicago-il/60608/weather-forecast/348308'
    '''
    tree = html.parse(accu_url)
    temp_f = tree.xpath("//div[@id='forecast-feed-3day-sponsor']//div[@class='info']//strong[@class='temp']")[0].text
    temp_cond = tree.xpath("//div[@id='forecast-feed-3day-sponsor']//div[@class='info']//span[@class='cond']")[0].text
    weather = {'temp': int(temp_f), 'cond': temp_cond}
    return weather


def draw_simple_scoreboard(gs_id_list, options={}):
    ''' Draw simple scoreboard from list of google scholar id
    '''
    fig = plt.gcf()
    fig.clf()
    
    params_cite = {'fontsize': 22, 'color': 'green', 'fontweight':'bold'}
    params_hindex = {'fontsize': 22, 'color': 'red', 'fontweight':'bold'}
    params_date = {'fontsize': 20, 'color': 'blue', 'fontweight':'bold'}
    params_others = {'fontsize': 30, 'color': 'black'}
    params_gini = {'fontsize': 20, 'color': 'blue', 'fontweight':'bold'}
    params_gini_val = {'fontsize': 20, 'color': 'black'}
    params_tweet = {'fontsize': 20, 'color': 'red', 'fontweight':'bold'}
    
    gs_all = get_all_scholar_matrix(gs_id_list) # get google scholar matrix
    gs_sort = sort_by_citation(gs_all)

    plt.text(0.2, 0.94, 'Citations', **params_cite)
    plt.text(0.5, 0.94, 'h-index', **params_hindex)
    plt.text(0.0, -0.1, 'Last citation update: ' + time.strftime('%X %b %d, %Y'), **params_date)
    plt.text(0.65, 0.6, 'Gini (citation)', **params_gini)
    plt.text(0.65, 0.53, 'Gini (h-index)', **params_gini)
    plt.text(0.92, 0.6, str(compute_gini(gs_sort.citation)), **params_gini_val)
    plt.text(0.92, 0.53, str(compute_gini(gs_sort.h_index)), **params_gini_val)
    
    if 'title' in options:
        fig.suptitle(str(options['title']), fontsize=35, fontweight='bold',
                      color='gray', style='italic')
    else:
        fig.suptitle('Google Scholar Scoreboard', fontsize=35, fontweight='bold',
                      color='gray', style='italic')
    
    plt.axis('off')
    # plot each name
    for i in range(len(gs_sort)):
        plt.text(-0.1, 0.85-0.07*i, str(gs_sort.first_name[i]) , **params_others)
        plt.text(0.2, 0.85-0.07*i, str(gs_sort.citation[i]), **params_others)
        plt.text(0.5, 0.85-0.07*i, str(gs_sort.h_index[i]), **params_others)
    
    if 'accuweather_link' in options:
        weather = get_accuweather_temp(options['accuweather_link'])
        plt.text(0.65, 0.7, weather['cond'], **params_others)
        plt.text(0.92, 0.7, str(weather['temp']) + ' F', **params_others)
    
    if 'img_link' in options:
        try:
            img_file = cStringIO.StringIO(urlopen(options['img_link']).read())
            img = Image.open(img_file)
            axicon = fig.add_axes([0.6,0.15,0.33,0.33])
            plt.imshow(img)
            plt.axis('off')
        except:
            None

        
    fig.canvas.draw()
    #fig.canvas.activateWindow()
    plt.axis('off')
    plt.draw()
    plt.show()
    


def start_scoreboard(gs_id_list, options={}):
    ''' Start Google Scholar Scoreboard that update every
        predefined interval
    '''
    plt.close('all')
    fig = plt.figure(facecolor='#FFFFE0')
    draw_simple_scoreboard(gs_id_list, options=options)
    return fig

    
def stop_scoreboard(timer):
    ''' Close all figure and stop timer '''
    timer.stop()
    plt.close('all')