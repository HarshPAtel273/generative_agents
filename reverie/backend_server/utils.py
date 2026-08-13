# LLM backend: local Ollama server (OpenAI-compatible API)
openai_api_key = "ollama"
openai_api_url = "http://localhost:11434/v1"
openai_api_model = "llama3.1:8b"

# Embedding backend: same Ollama server
openai_api_embedding_key = "ollama"
openai_api_embedding_url = "http://localhost:11434/v1"
openai_api_embedding_model = "nomic-embed-text"

key_owner = "Falguni"

maze_assets_loc = "../../environment/frontend_server/static_dirs/assets"
env_matrix = f"{maze_assets_loc}/the_ville/matrix"
env_visuals = f"{maze_assets_loc}/the_ville/visuals"

fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"

collision_block_id = "32125"

debug = False
