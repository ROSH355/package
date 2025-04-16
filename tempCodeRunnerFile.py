def get_course_completion_status(user_id, course_id):
#     # Call the stored procedure to get the course completion status
#     result = db.session.execute(
#         text("CALL get_course_completion_status(:user_id, :course_id)"),
#         {"user_id": user_id, "course_id": course_id}
#     ).fetchone()

#     if result:
#         return result[0]  # Assuming the stored procedure returns a status like 'Completed' or 'In Progress'
#     return None