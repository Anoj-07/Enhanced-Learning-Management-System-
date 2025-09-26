from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_course_description(course_name, difficulty_level):
  completion = client.chat.completions.create(
      model="openai/gpt-oss-20b",
      messages=[
        {
          "role": "system",
          "content": "Act as the Description writer of course by course name and its difficulty level"
        },
        {
          "role": "user",
          "content": "write the description of course by its course name and its difficulty level \nname: Python\ndifficulty_level : Beginner\n"
        },
        {
          "role": "assistant",
          "content": "**Python – Beginner**\n\nEmbark on your programming journey with this beginner‑friendly Python course designed to lay a solid foundation in one of the world’s most popular and versatile programming languages. From understanding basic syntax and data types to mastering control structures, functions, and simple object‑oriented concepts, this course guides you step‑by‑step through hands‑on exercises and real‑world examples. Ideal for complete newcomers, it emphasizes clarity, practice, and problem‑solving, ensuring you build confidence before moving on to more advanced topics. Whether you’re looking to launch a career in software development, data science, or automation, this Python course equips you with the essential tools and mindset to start coding today."
        },
        {
          "role": "user",
          "content": ""
        }
      ],
      temperature=1,
      max_completion_tokens=8192,
      top_p=1,
      reasoning_effort="medium",
      stream=True,
      stop=None
  )

  return completion.choices[0].message.content


