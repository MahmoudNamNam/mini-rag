from string import Template

#### RAG PROMPTS ####

#### System ####
system_prompt = Template("\n".join([
    "You are an assistant tasked with generating a response for the user.",
    "But answers in Bullets if you can"
    "You will be provided with a set of documents related to the user's query.",
    "Your response must be based solely on the content of the provided documents.",
    "Ignore any documents that are not relevant to the user's query.",
    "You may politely apologize if you're unable to generate a relevant response.",
    "Ensure your response is in the same language as the user's query.",
    "Be polite and respectful to the user.",
    "Be precise and concise. Avoid including unnecessary information."
]))

#### Document ####
document_prompt = Template("\n".join([
    "## Document No: $doc_num",
    "### Content:",
    "$chunk_text"
]))

#### Footer ####
footer_prompt = Template("\n".join([
    "Based solely on the above documents, please generate a response to the user query.",
    "## Quetsion:",
    "$query",
    "",
    "## Answer:"
]))
