from mietmatrix_viewer import MietmatrixViewer


if __name__ == "__main__":
    file_path = r"C:\llm-project\data\raw\mietmatrix.csv"

    viewer = MietmatrixViewer(file_path)
    viewer.load()
    df = viewer.get_view()
    df.to_csv("out.csv", index=False)
    print(df)
