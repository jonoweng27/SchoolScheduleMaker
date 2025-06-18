def smart_title(s):
    """Capitalize each word except 'of' (unless it's the first word)."""
    if not isinstance(s, str):
        return s
    words = s.strip().split()
    return ' '.join(
        w.capitalize() if i == 0 or w.lower() != 'of' else 'of'
        for i, w in enumerate(words)
    )

def normalize_dataframe(df, value_columns=None):
    """
    Smart-title all column names, and smart-title values in value_columns.
    """
    # Smart-title all column names
    df = df.rename(columns=lambda c: smart_title(c))
    # Smart-title values in specified columns
    if value_columns:
        for col in value_columns:
            if col in df.columns:
                df[col] = df[col].apply(smart_title)
    return df