import praw
from requests import Session
from time import sleep
from fake_useragent import UserAgent
from praw.exceptions import RedditAPIException
from llm.main import create_response
from auth.bots import create_log

class RedditBot:
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        username: str = None,
        password: str = None,
        user_agent: str = None,
        log_file: str = None,
        bot_id:str  = None,
        user_id:str = None,
    ) -> None:
        session = Session()

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent or UserAgent().random,
            requestor_kwargs={"session": session}
        )
        self.log_file = log_file or "commented_posts.txt"
        self.user_id = user_id
        self.bot_id = bot_id
        
        print(self.user_id)
        print(self.bot_id)

    def login(self) -> None:
        try:
            print("[LOGIN] - Logged in as {}".format(self.reddit.user.me()))
            create_log(log="[LOGIN] - Logged in as {}".format(self.reddit.user.me()), user_id=self.user_id, bot_id=self.bot_id)
        except Exception as e:
            print("[LOGIN] - Failed to log in: {}".format(e))
            create_log(log="[LOGIN] - Failed to log in: {}".format(e), user_id=self.user_id, bot_id=self.bot_id)

    def get_trending_topics(self) -> list[praw.models.Submission]:
        trending_topics = []
        commented_posts = self.load_commented_posts()
        
        for submission in self.reddit.subreddit("all").hot(limit=500):
            if submission.id not in commented_posts:
                trending_topics.append(submission)

        return trending_topics

    def extract_text_title(self, submission: praw.models.Submission) -> str:
        return submission.title

    def extract_text_content(self, submission: praw.models.Submission) -> str:
        return submission.selftext

    def extract_comment_content_and_upvotes(
        self, submission: praw.models.Submission
    ) -> list[tuple[str, int]]:
        
        submission.comments.replace_more(limit=0)
        comments = submission.comments.list()
        comment_content_and_upvotes = []
        for comment in comments:
            comment_content_and_upvotes.append((comment.body, comment.score))
        return comment_content_and_upvotes

    def generate_comment(
        self,
        submission: praw.models.Submission,
        title: str,
        post_text: str,
        comments: list[tuple[str, int]],
    ) -> None:
        comments = sorted(comments, key=lambda comment: comment[1], reverse=True)
        if len(comments) >= 4:
            comments = comments[:4]
        else:
            comments = comments[: len(comments)]
        comments = [comment[0] for comment in comments]
        comments = ", ".join(comments)
        
        prompt = f'''
        [SYSTEM] You are an avid Reddit user skilled at crafting concise and engaging comments that resonate with the community and garner significant upvotes. Your task is to generate a comment that seamlessly integrates with the existing discussion, mirroring the tone and sentiment of the most popular comments. Your comment should be succinct yet intriguing, capturing the attention of readers without appearing overly verbose or excessively friendly. Avoid being aggressive or offensive at all costs.

        [CONTENT] The post titled "{title}" contains the following text: "{post_text}". Among the most upvoted comments are: "{comments}". Your objective is to create a comment that aligns with the prevailing mood and opinions expressed in the thread. Keep your response natural and in line with the community's language and attitudes.

        Format your response as a single, short phrase. Example comments may provide helpful guidance in crafting your response. Aim for a balance between simplicity and sophistication to engage readers effectively. 

        [CONTENT]
        '''
                
        new_prompt = str(prompt)
        
        comment = create_response(post=new_prompt)
        try:
                submission.reply(comment)
                print("[SUCCESS] - replied to the post!")
                create_log(log="[SUCCESS] - replied to the post", user_id=self.user_id, bot_id=self.bot_id)
                exit = True
        except RedditAPIException as e:
                if e.error_type == "RATELIMIT":
                    print("[RATE LIMIT] - rate limited sleeping 10 mins")
                    create_log("[RATE LIMIT] - rate limited sleeping for 30", user_id=self.user_id, bot_id=self.bot_id)
                    
                elif e.error_type == "THREAD_LOCKED":
                    print("Thread locked. Skipping.")
                    create_log(log="thread locked skipping", user_id=self.user_id, bot_id=self.bot_id)
                else:
                    print(e.error_type)
                    create_log(e.error_type, user_id=self.user_id, bot_id=self.bot_id)

        print(f"Replied to '{submission.title}' with '{comment}'")
        create_log(log=f"Replied to '{submission.title}' with '{comment}'", user_id=self.user_id, bot_id=self.bot_id)
                
    def load_commented_posts(self) -> list[str]:
        try:
            with open(self.log_file, "r") as f:
                commented_posts = f.read().splitlines()
        except FileNotFoundError:
            commented_posts = []
        return commented_posts

    def log_commented_post(self, post_id: str) -> None:
        with open(self.log_file, "a") as f:
            f.write(post_id + "\n")

    def run(self) -> None:
        self.login()
        trending_topics = self.get_trending_topics()
        print("[SUCCESS] - fetched a trending topic!")
        create_log(log="SUCCESS] - fetched a trending topic", user_id=self.user_id, bot_id=self.bot_id)
        for submission in trending_topics:
            post_title = self.extract_text_title(submission)
            print("SUCCESS] - received title")
            create_log(log="SUCCESS] - received title", user_id=self.user_id, bot_id=self.bot_id)
            text_content = self.extract_text_content(submission)
            print("SUCCESS] - received content")
            create_log(log="SUCCESS] - received content", user_id=self.user_id, bot_id=self.bot_id)
            comment_content_and_upvotes = self.extract_comment_content_and_upvotes(submission)
            self.generate_comment(submission, post_title, text_content, comment_content_and_upvotes)
            create_log(log="GOING TO SLEEP FOR 30 MINS NOW", user_id=self.user_id, bot_id=self.bot_id)
            
            print("process completed")
            
        return True
            