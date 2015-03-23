# WhoseTurn

## Situation:

N people sitting in the office ordering food every day.
Each day, another person is responsible for gathering orders and calling the desired catering service.

**Problem: whose turn is it to call next? :)**

**Solution**, a table (in our case on the whiteboard in the office), where each person is listed and starts with 0 points.
Every time a person eats and someone else ordered, he gets 1 point.
Every time a person does the ordering, he gets M points deducted where M is the number of people he did the ordering for.
Person(s) with the highest number of points are next.

I've used this real-life situation as a little project to learn/experiment with python, tornado web framework, websockets...

How to install/configure is written in INSTALL.md file.

## STANDARD WARNING: this is a demo-exercise code. A whole ecosystem of dangerous bugs contained within.
