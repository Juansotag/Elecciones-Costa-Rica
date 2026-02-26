
import pandas as pd
import numpy as np
import os
import json

def process():
    file_path = 'Scrapping data v2.xlsx'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    xl = pd.ExcelFile(file_path)
    
    def standardize_df(df, platform, mapping, id_col):
        df = df.copy().rename(columns=mapping)
        df['platform'] = platform
        
        # Determine fecha_pub column
        p_col = 'fecha_pub' if 'fecha_pub' in df.columns else ('createdat' if 'createdat' in df.columns else None)
        if p_col:
            df['fecha_pub'] = pd.to_datetime(df[p_col], errors='coerce', dayfirst=True).dt.tz_localize(None)
        
        df['fecha_ext'] = pd.to_datetime(df['fecha_ext'], errors='coerce', dayfirst=True).dt.tz_localize(None)
        df['internal_post_id'] = platform + "_" + df[id_col].astype(str)
        
        common_cols = ['internal_post_id', 'platform', 'fecha_pub', 'fecha_ext', 'likes', 'comments', 'shares']
        return df[[c for c in common_cols if c in df.columns]]

    fb_map = {'megusta': 'likes', 'comentarios': 'comments', 'compartidas': 'shares'}
    ig_map = {'megusta': 'likes', 'comentarios': 'comments'}
    tk_map = {'megusta': 'likes', 'comentarios': 'comments', 'compartidos': 'shares'}
    tw_map = {'likecount': 'likes', 'replycount': 'comments', 'retweet_count': 'shares'}

    clean_fb = standardize_df(pd.read_excel(xl, 'Facebook'), 'Facebook', fb_map, 'postId')
    clean_ig = standardize_df(pd.read_excel(xl, 'Instagram'), 'Instagram', ig_map, 'postId')
    clean_tk = standardize_df(pd.read_excel(xl, 'TikTok'), 'TikTok', tk_map, 'id')
    clean_tw = standardize_df(pd.read_excel(xl, 'Twitter'), 'Twitter', tw_map, 'id')

    df_all = pd.concat([clean_fb, clean_ig, clean_tk, clean_tw], ignore_index=True)
    for col in ['likes', 'comments', 'shares']:
        if col in df_all.columns:
            df_all[col] = pd.to_numeric(df_all[col], errors='coerce').fillna(0)
    
    df_all['total_int'] = df_all.get('likes', 0) + df_all.get('comments', 0) + df_all.get('shares', 0)
    df_all = df_all.sort_values(['internal_post_id', 'fecha_ext'])
    
    # Growth calculation
    df_all['growth'] = df_all.groupby('internal_post_id')['total_int'].diff().fillna(0)
    
    # Q1: Decay days
    # Days since pub until last growth > 0
    def calc_decay(group):
        growth_days = group[group['growth'] > 0]
        if growth_days.empty:
            return 0
        last_growth_date = growth_days['fecha_ext'].max()
        pub_date = group['fecha_pub'].min()
        if pd.isna(pub_date):
            return 0
        return (last_growth_date - pub_date).days

    decay_series = df_all.groupby('internal_post_id').apply(calc_decay)
    
    print(f"RESULT_MEAN_DECAY: {decay_series.mean():.2f}")
    print(f"RESULT_MAX_DECAY: {decay_series.max():.2f}")
    
    # Q2: Election impact
    # Election date: 2026-02-01
    election_date = pd.Timestamp('2026-02-01')
    df_all['is_post_election'] = df_all['fecha_pub'] >= election_date
    
    # Filter for Laura Fernandez (winner)
    # We need usernames/names from original sheets or Candidates sheet
    # For now, let's assume 'Username' or 'name' contains the candidate info
    # Let's get the mappings of internal_post_id to Candidate from Facebook sheet as example
    fb_orig = pd.read_excel(xl, 'Facebook')
    fb_orig['internal_post_id'] = "Facebook_" + fb_orig['postId'].astype(str)
    post_to_user = fb_orig.set_index('internal_post_id')['Username'].to_dict()
    
    # Also for others
    for platform, sheet, id_col, user_col in [('Instagram', 'Instagram', 'postId', 'Username'), 
                                               ('TikTok', 'TikTok', 'id', 'name'),
                                               ('Twitter', 'Twitter', 'id', 'name')]:
        orig = pd.read_excel(xl, sheet)
        orig['internal_post_id'] = platform + "_" + orig[id_col].astype(str)
        post_to_user.update(orig.set_index('internal_post_id')[user_col].to_dict())

    df_all['User'] = df_all['internal_post_id'].map(post_to_user)
    
    # Winner: Laura Fernández Delgado
    winner_name = "Laura Fernández Delgado"
    
    # Compare decay for pre vs post election posts
    df_decay = df_all.groupby(['internal_post_id', 'User', 'is_post_election']).apply(calc_decay).reset_index()
    df_decay.columns = ['internal_post_id', 'User', 'is_post_election', 'decay_days']
    
    summary_winner = df_decay[df_decay['User'].str.contains('Laura', na=False)].groupby('is_post_election')['decay_days'].mean()
    summary_others = df_decay[~df_decay['User'].str.contains('Laura', na=False)].groupby('is_post_election')['decay_days'].mean()
    
    print(f"WINNER_DECAY: {summary_winner.to_dict()}")
    print(f"OTHERS_DECAY: {summary_others.to_dict()}")

if __name__ == "__main__":
    process()
