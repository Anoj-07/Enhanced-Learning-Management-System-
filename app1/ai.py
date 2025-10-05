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
          "content": f"write the description of course by its course name {course_name} and its difficulty level {difficulty_level} and only return the description without any other text"
        },
      ],
      temperature=1,
      max_completion_tokens=1024,
      top_p=1,
      stream=False,
      stop=None
  )

  return completion.choices[0].message.content


