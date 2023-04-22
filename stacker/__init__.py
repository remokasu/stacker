import os

# リソースフォルダへのパスを取得する
resource_path = os.path.join(os.path.dirname(__file__), 'data')

plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')

# モジュールにパスを追加する
__path__.append(resource_path)
__path__.append(plugins_path)