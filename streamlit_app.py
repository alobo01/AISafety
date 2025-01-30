import streamlit as st
import os
from urllib.parse import urlencode
# import debugpy


# Start the remote debugger (listen on a specific port)
# def start_debugger():
#     debugpy.listen(("0.0.0.0", 5678))  # Adjust the port as needed
#     print("Remote debugger is listening on port 5678")
#     debugpy.wait_for_client()  # Optional: Wait for the debugger to attach
#     print("Debugger attached")

# Uncomment this line to activate the debugger
# start_debugger()

# Helper function to load posts
def load_posts(folder):
    posts = []
    for subfolder in os.listdir(folder):
        subfolder_path = os.path.join(folder, subfolder)
        if os.path.isdir(subfolder_path):
            main_md = os.path.join(subfolder_path, 'main.md')
            if os.path.exists(main_md):
                with open(main_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                posts.append({
                    'title': subfolder,
                    'content': content,
                    'media_folder': os.path.join(subfolder_path, 'media')
                })
    return posts

# Load posts
POSTS_FOLDER = 'posts'  # Folder containing subfolders with posts
posts = load_posts(POSTS_FOLDER)

# Configure page
st.set_page_config(page_title="AI Safety Blog", page_icon=":robot_face:", layout="wide")

# Header with logo and navigation
with st.container():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("logo.png", width=100)  # Add your logo here
    with col2:
        st.markdown("""
        # AI Safety Blog
        ### Exploring research, concerns, and interests in AI safety
        
        [LinkedIn](https://www.linkedin.com/in/antonio-lobo-a78003234/) | [CV](#cv)
        """)

# Navigation bar
st.sidebar.title("Navigation")
for post in posts:
    params = urlencode({"post": post['title']})
    st.sidebar.markdown(f"[**{post['title']}**](?{params})")

# Main content
query_params = st.query_params
selected_post_title = query_params.get("post", None)
isCodeBlock = False
codeLanguage = None
codeBlock =""
if selected_post_title:
    # Display selected post
    selected_post = next((post for post in posts if post['title'] == selected_post_title), None)
    if selected_post:
        st.title(selected_post['title'])
        if os.path.exists(selected_post['media_folder']):
            final_markdown = selected_post['content'].replace("media/", f"{selected_post['media_folder'].replace("\\","/")}/")
        else:
            final_markdown = selected_post['content']
        for line in final_markdown.split("\n"):
            if line.startswith("!["):
                st.image(line.split("(")[1].split(")")[0])
            elif line.startswith("```") and isCodeBlock:
                isCodeBlock=False
                st.code(codeBlock, wrap_lines=True, language=codeLanguage)
                codeBlock = ""
                codeLanguage = None
            elif line.startswith("```") and not isCodeBlock:
              isCodeBlock=True
              codeLanguage = line.split("```")[1]
            elif isCodeBlock:
              codeBlock+=line+"\n"
            else:
                st.markdown(line)
    else:
        st.error("Post not found.")
else:
    # Home page with CV
    st.markdown("## Welcome to the AI Safety Blog")
    st.markdown("""
    This blog features research, concerns, and insights in the field of AI safety. Navigate through the posts using the sidebar.
    """)
    st.markdown("""
    ## About Me
    ### Antonio Lobo Santos
    - **Location**: Barcelona, Spain
    - **Email**: [alobosantos10@gmail.com](mailto:alobosantos10@gmail.com)
    
    ### Professional Summary
    Passionate Backend Developer with extensive experience in event-driven microservices architecture, AI-related technologies, and database management. Demonstrated expertise in Python, NESTJS, and Kubernetes, complemented by a strong academic background in Computer Engineering and Mathematics. Dedicated to delivering high-quality, scalable solutions and continuously enhancing technical skills.

    Deeply interested in researching the synergy between large language models (LLMs) and knowledge graphs for advancing AI explainability. Actively engaged in exploring AI ethics and alignment, with a strong commitment to contributing to research in this critical field.

    ### Work Experience
    - **Senior Backend Developer**  
      *Axión* (Seville, July 2021 - July 2023)  
      Spearheaded the development and maintenance of a robust, event-driven microservices architecture.  
      Integrated advanced technologies such as NESTJS, Python, Apache Kafka, and ElasticSearch to enhance system performance.  
      Optimized deployment processes using Docker, Kubernetes, and GitLab-CI, ensuring seamless continuous integration and deployment.  
      Managed and scaled both relational and non-relational databases to support high-traffic applications.

    - **Technical Coordinator, Web Design**  
      *Becomdigital* (Seville, April 2020 - January 2021)  
      Led a team of developers to design and implement WordPress-based solutions for small businesses impacted by the COVID-19 pandemic.  
      Provided strategic direction and technical oversight to ensure project success.

    - **App Developer (Extracurricular)**  
      *High School Project* (Seville, September 2017 - June 2019)  
      Directed the development of two innovative mobile applications: *Stop Cyberbullying* and *Smart Huerto*, both of which gained recognition on the MIT App Inventor Gallery.

    ### Education
    - **Master in Artificial Intelligence**  
      *UB-UPC-URV, Barcelona, Spain* (2024 - 2025)  
      Focused on LLMs, Knowledge Engineering, and multi-agent systems.

    - **Double Degree in Computer Engineering and Mathematics**  
      *University of Seville, Seville, Spain* (2019 - 2024)  
      Intern student at the AI department.  
      Selected for SICUE Program, completing the third year at the University of Malaga.

    - **Technological High School Diploma**  
      *IES ISBILYA, Seville, Spain* (September 2017 - June 2019)  
      Achieved candidacy for the Outstanding Award in 2019.

    ### Certifications and Courses
    - **Bluedot AI Alignment Course**  
      (November 2024)  
      Selected participant in an intensive program focusing on AI safety, alignment, governance, and ethics.  
      Acquired knowledge about preventing catastrophic risks associated with future AI systems.  
      Developed connections and skills to contribute to long-term AI safety research and policy-making efforts.  
      [Course details](https://aisafetyfundamentals.com/)

    ### Internships and Projects
    - **Intern, CSIC - Instituto de Inteligencia Artificial**  
      (November 2024 - Present)  
      Conducting research on AI verification techniques to ensure the reliability and safety of AI systems.  
      Exploring methodologies to validate and verify complex AI models in alignment with cutting-edge AI safety principles.
      Exploring geometric interpretation of transformers embedding during text generation.

    - **Intern, Sputnik321 Project**  
      *321Sputnik, Seville, Spain* (2020 - 2021)  
      Collaborated in the training of young entrepreneurs, providing technical guidance and support in various entrepreneurial initiatives.

    ### Publications
    - [El infinito: algunas curiosidades y su enseñanza en Secundaria y Bachillerato](https://scpmluisbalbuena.org/autor/lobo-santos-antonio/)
    - [Construyendo el "mapamático"](https://thales.cica.es/epsilon_d9/sites/default/files/2023-09/epsilon114_04.pdf)

    ### Languages
    - **English:** C1 (certAcles)
    - **French:** DELF B2
    """)
