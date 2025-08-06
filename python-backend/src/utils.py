def smart_title(s):
    """
    Capitalize each word except 'of' (unless it's the first word).
    Also, keep all-uppercase words (like 'AP') and capitalize all letters after slashes or parentheses.
    """
    if not isinstance(s, str):
        return s

    def cap_word(w, i):
        # Keep all-uppercase words (like 'AP')
        if w.isupper():
            return w
        # Don't lowercase 'of' unless it's not the first word
        if i != 0 and w.lower() == 'of':
            return 'of'
        # Capitalize after slashes or parentheses
        parts = []
        start = 0
        for j, c in enumerate(w):
            if c in '/(':
                if start < j:
                    parts.append(w[start:j].capitalize())
                parts.append(c)
                start = j + 1
        if start < len(w):
            parts.append(w[start:].capitalize())
        return ''.join(parts) if parts else w.capitalize()

    words = s.strip().split()
    return ' '.join(
        cap_word(w, i) for i, w in enumerate(words)
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