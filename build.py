#!/usr/bin/env python3
"""Build the Pathfinders Advisors static site into ./site (GitHub Pages ready).

Usage:  python3 build.py            # review build (noindex)
        python3 build.py --live     # launch build (indexable)

Only the Python standard library is used. Page bodies live in src/pages/*.html and
use {{TOKENS}} that are filled in here, so the header, footer, schema, reviews,
workshops, articles and FAQs come from one place.
"""
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC = ROOT_DIR / "src" / "pages"
OUT = ROOT_DIR / "site"
LIVE = "--live" in sys.argv

SITE = "https://www.pathfindersadvisors.com"
WP = SITE + "/wp-content/uploads/"
BOOK_URL = "https://link.insiderhub.co/widget/bookings/pf-advising-session"
WORKSHOP_URL = "https://workshop.pathfindersadvisors.com/"
VIDEO_URL = WP + "2026/10/College-Planning-for-Families.mp4"
LOGO = WP + "2025/01/Pathfinders_hor_RGB.png"
LOGO_600 = WP + "2025/01/Pathfinders_hor_RGB-600x126.png"
LOGO_300 = WP + "2025/01/Pathfinders_hor_RGB-300x63.png"
LOGO_STACK = WP + "2025/01/Pathfinders_stack_RGB.png"
ORG_NAME = "Pathfinders College & Career Advisors"
SOCIAL = {
    "facebook": "https://www.facebook.com/incollegeplanning/",
    "instagram": "https://www.instagram.com/pathfindersadvisors",
    "linkedin": "https://www.linkedin.com/company/pathfinders-college-career-advisors",
    "youtube": "https://www.youtube.com/@PathfindersAdvisors",
}
NOW = dt.datetime.now(dt.timezone.utc)
VERSION = NOW.strftime("%Y%m%d%H%M%S")

e = lambda s: html.escape(s, quote=True)  # noqa: E731

# --------------------------------------------------------------------------- icons
ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "school": '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/><path d="M22 10v6"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><path d="m16.24 7.76-2.12 6.36-6.36 2.12 2.12-6.36z"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    "gift": '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 8a2.5 2.5 0 0 1 0-5C11 3 12 8 12 8s1-5 4.5-5a2.5 2.5 0 0 1 0 5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "dollar": '<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "bar": '<path d="M12 20V10M18 20V4M6 20v-4"/>',
    "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="m22 8-6 4 6 4z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "map": '<path d="M9 3 3 6v15l6-3 6 3 6-3V3l-6 3-6-3z"/><path d="M9 3v15M15 6v15"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "play": '<path d="M8 5v14l11-7z" fill="currentColor" stroke="none"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
    "check": '<path d="M5 12.5 9.5 17 19 7.5"/>',
    "heart": '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z"/>',
}
SOCIAL_ICONS = {
    "facebook": '<path fill="currentColor" d="M14 8.5V6.8c0-.8.5-1 .9-1h2.4V2.1L14 2c-3.6 0-4.4 2.7-4.4 4.4v2.1H7.5v3.8h2.1V22h4.4v-9.7h3l.4-3.8H14z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/>',
    "linkedin": '<path fill="currentColor" d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.5h4V21H3zM9.5 9.5h3.8v1.6h.1c.5-1 1.8-2 3.8-2 4 0 4.8 2.6 4.8 6V21h-4v-5.2c0-1.2 0-2.9-1.8-2.9s-2 1.4-2 2.8V21h-4z"/>',
    "youtube": '<path fill="currentColor" d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8zM9.75 15.02V8.98L15.5 12l-5.75 3.02z"/>',
}


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            + ICONS[name] + "</svg>")


ROUTE_SVG = """<div class="hero-route route-draw" aria-hidden="true"><svg viewBox="0 0 1440 640" preserveAspectRatio="xMidYMid slice" fill="none">
<g stroke="rgba(157,188,198,.16)" stroke-width="1.2">
<ellipse cx="1210" cy="540" rx="330" ry="190" transform="rotate(-12 1210 540)"/>
<ellipse cx="1210" cy="540" rx="250" ry="138" transform="rotate(-12 1210 540)"/>
<ellipse cx="1210" cy="540" rx="170" ry="90" transform="rotate(-12 1210 540)"/>
<ellipse cx="1210" cy="540" rx="92" ry="46" transform="rotate(-12 1210 540)"/>
<ellipse cx="160" cy="70" rx="260" ry="120" transform="rotate(8 160 70)"/>
<ellipse cx="160" cy="70" rx="180" ry="78" transform="rotate(8 160 70)"/>
<ellipse cx="160" cy="70" rx="100" ry="40" transform="rotate(8 160 70)"/>
</g>
<path d="M-40 590 C 200 560 250 430 460 440 S 760 590 960 450 S 1200 170 1490 130" stroke="rgba(246,163,94,.75)" stroke-width="2.4" stroke-linecap="round"/>
<g fill="#F6A35E"><circle cx="960" cy="450" r="5"/><circle cx="1262" cy="226" r="5"/></g>
<g fill="none" stroke="rgba(246,163,94,.5)" stroke-width="1.5"><circle cx="960" cy="450" r="12"/><circle cx="1262" cy="226" r="12"/></g>
</svg></div>"""

# --------------------------------------------------------------------------- data
GOOGLE_REVIEWS = [
    ("Stephanie Mckinnon", "Aaron was very helpful as we navigated high school in preparation for college applications for our oldest son. He assisted with class schedule recommendations (such as foreign language planning), he provided specific guidance around building his college “resume,” and he also spent a significant amount of time between 9th and 11th grades helping my son identify his career path in advance of college applications. As we approached senior year he managed our timeline and kept us ahead of application deadlines. He provided guidance, review and feedback of my son’s college essay. He provided recommendations on when to set up campus tours. He talked with us about ensuring our college debt was in alignment with future career income expectations. At the end, I’m thrilled to share that my son was accepted to every university that he applied to, and I do believe we have Aaron to thank for much of this success!"),
    ("Megan Hauck", "Our daughter, who is currently in her junior year of high school, has been working with Aaron to prepare for college. Aaron has been so knowledgeable throughout this whole process, from prepping for college applications to narrowing her search for a college that fits all her (and our family’s) needs. Throughout this process we have been comfortable and confident that we will find the perfect fit! I would highly recommend Pathfinders!"),
    ("Becky J", "Our family started working with Aaron Green at Pathfinders in my son's sophomore year and it has been a valuable experience. He worked closely with our son to help him identify the career path for him and then went through a very thorough process of researching schools and setting him up for success with applications. Aaron's guidance through the entire process has made it much less stressful for us as parents and for my son as the student. My son has committed to his college of choice and feels confident about that. I highly recommend Aaron and the Pathfinder team!!"),
    ("Mitch Artist", "Fantastic service! They helped my son save thousands on college, and fully understand his future."),
    ("Shannon Hutson", "The Pathfinders Team made a big difference for our daughter, and for our whole family. They helped us think clearly about her future wants and guided us through the steps she needed to get there. Their career readiness process was incredibly valuable and gave us real confidence in the decisions she was making along the way. I highly recommend for any high schooler!"),
    ("Kaleigh Eckler", "Aaron really helped us think about degrees differently and consider what our son really wants to do. He showed us how that relates to the right college. I recommend having a family call!"),
]

QUOTES = {
    "doug": dict(name="Doug Stevens", meta="Parent, daughter accepted to The Ohio State University",
                 text="Working with Pathfinders was a game-changer for our family, turning what could’ve been a very intimidating, time-consuming and stressful experience into an enlightening, empowering and uplifting one. From the very start, Aaron patiently walked us through every step of the college admissions process. He quickly built a strong rapport with our daughter, taking the time to get a well-rounded understanding of her career ambitions, college expectations, strengths, and interests—both in and out of the classroom. Together, they developed a comprehensive plan and timeline that ensured all important deadlines were met (ACT/SAT tests, applications, FAFSA), while also creating a solid list of colleges that were a good fit for our daughter. Thanks to Aaron’s expertise and personalized approach, we confidently navigated the entire college admissions journey – culminating in our daughter’s acceptance to THE Ohio State University where she’ll pursue a Bachelor of Science in Aviation (Go Bucks!). The investment in Pathfinder’s services was absolutely worth every penny. The peace of mind that Aaron provided with his personalized attention, expert guidance, on-going support and encouragement, far exceeded our expectations."),
    "devita": dict(name="Devita Strand", meta="Parent of Carl, CL Class of 2019",
                   text="I knew this would be the best fit for Carl and our family after a lot of research, and then meeting in person. The advisors were amazingly patient and encouraging with Carl. He’s on the autism spectrum, which posed some unique challenges in the process, but they were able to provide the individualized career planning and college admissions support he needed."),
    "kathy": dict(name="Kathy Abbott", meta="Parent of Trixie, CL Class of 2019",
                  text="Thank you! This is perhaps the best business I’ve come across in a long time...I had interviewed other “college counselling” companies but they didn’t offer the professionalism and decision making structure you offer. As soon as our daughter started the program, my anxiety went down by about 80 percent and I know she felt better. She also made her final decision based on the value framework you laid out for us. We’re smart enough to know we had no idea how to choose a college, and we are immensely happy with the decision Trixie made thanks to everyone."),
    "miranda": dict(name="Miranda Barrett", meta="Parent, Arlington, VA",
                    text="Working with Pathfinders Advisors has been an absolute game-changer for our family during the college planning process. Their advisor, Aaron, brings a steady hand to what can often feel like an overwhelming and emotional journey, providing calm and organization every step of the way. What stood out most was how incredibly likable and relatable he is with my teenage son, building a connection that makes my son feel heard and understood. Aaron's thoughtful guidance is turning a stressful time into a manageable and even enjoyable experience. I can’t recommend them enough to any family navigating this challenging milestone of preparing to launch a kid!"),
}

# (title, ISO start with US Eastern offset, display time)
WORKSHOPS = [
    ("College Financial Aid", "2026-08-20T19:30:00-04:00", "7:30 PM EST"),
    ("College Planning Strategy", "2026-09-17T19:00:00-04:00", "7:00 PM EST"),
    ("Education Investment Planning", "2026-10-13T11:30:00-04:00", "11:30 AM EST"),
    ("College Admissions", "2026-11-19T19:00:00-05:00", "7:00 PM EST"),
    ("Career & College Planning", "2026-12-13T18:00:00-05:00", "6:00 PM EST"),
]

# Every post from the old WordPress site (tools/import_posts.py), newest first.
# Fields: title, slug, date, image (full URL), alt, topics, excerpt.
POSTS = json.loads((ROOT_DIR / "src" / "data" / "posts.json").read_text(encoding="utf-8"))
ARTICLES = [(x["title"], x["slug"], x["date"], x["image"], x["alt"], x["topics"], x["excerpt"]) for x in POSTS]
CATEGORIES = ["Current Events", "Financial", "Careers", "ACT/SAT"]
_KW = ROOT_DIR / "src" / "data" / "article_keywords.json"
ARTICLE_KEYWORDS = json.loads(_KW.read_text()) if _KW.exists() else {}
# The three articles the old financial planners page showed, in its order.
PLANNER_ARTICLES = ["the-biggest-financial-decision-most-advisors-arent-leading",
                    "why-financial-aid-appeals-are-the-most-overlooked-opportunity-in-college-planning",
                    "understanding-the-css-profile-what-it-is-and-why-it-matters-for-college-aid"]

GUIDES = [
    ("College Application Timeline & Checklist", WP + "2026/06/College-Application-Timeline-Checklist-600x347.png", "Every deadline from junior spring to decision day, in one printable checklist."),
    ("A Parent’s Cheat Sheet to Standardized Tests for College Admission", WP + "2026/06/A-Parents-Cheat-Sheet-to-Standardized-Tests-for-College-Admission-600x333.png", "SAT, ACT and PSAT explained in plain language, including when each one matters."),
]

FAQS = [
    ("Can't we figure this out ourselves?",
     ["You can, but families don't know what they don't know, and mistakes in college and career planning can be expensive and difficult to reverse.",
      "Just as you work with a financial advisor for major financial decisions, Pathfinders helps you avoid costly education mistakes before they happen."]),
    ("Isn't this what the school counselor does?",
     ["School counselors are valuable, but they often support hundreds of students. Pathfinders provides personalized, career-first planning that brings together career exploration, educational fit, financial strategy and ongoing guidance throughout the process."]),
    ("Our child will figure it out once they're in college. Why plan now?",
     ["That may have been true 20 years ago. Today, changing majors, transferring schools or extending graduation can significantly increase costs and delay financial independence.",
      "Starting with career clarity helps students make more informed decisions from the beginning."]),
    ("Is this only for students applying to elite colleges?",
     ["No. Students attending all types of colleges deserve clarity, not just students attending elite colleges. The process begins with career discovery and then identifies the best educational pathway, which may be a four-year university, community college, trade school, apprenticeship, military service or another option."]),
    ("Will my teenager actually engage?",
     ["Yes. Students work directly with experienced advisors who help them take ownership of the process, which often reduces parent-child tension."]),
    ("Is it worth the investment?",
     ["The cost of expert guidance is small compared with the financial impact of choosing the wrong educational path or taking on unnecessary student debt.",
      "Families who work with us save about $56,000 on average through scholarship strategies, four-year graduation planning, internships and co-op opportunities."]),
    ("When should our family start?",
     ["It's never too late. Many families start in 9th or 10th grade, so there is time for career discovery before applications. Most reach out when sophomore or junior year begins and the timeline suddenly feels real, and that is still a great time to start.",
      "Seniors can still get help with their college list and essays, as well as applications, financial aid and choosing between offers. We also work with students who are already in college or considering an advanced degree."]),
    ("What happens on the complimentary family strategy call?",
     ["We meet your family where you are in the college and career journey. Our focus is a conversation with your student, where we learn about their interests, strengths, and goals, point out common blind spots that derail many students, and answer the big question: What should we do next? Most families leave that conversation having learned more about their student's career thoughts than they knew before the call."]),
    ("Do you work with families outside your area?",
     ["Yes. Coaching, the online College & Career Planning Course and our workshops are all virtual, so we work with families across the United States."]),
]

FP_FAQS = [
    ("Will Pathfinders compete with my services?",
     ["No. Pathfinders complements financial planning by focusing on career discovery and education strategy, so you remain the family's primary financial strategist."]),
    ("Will my clients value this?",
     ["Yes. Education planning is one of the most emotionally and financially significant decisions a family faces, and clients appreciate proactive guidance on it."]),
    ("Will this create more work for me?",
     ["No. Pathfinders handles the specialized planning while keeping you informed, which strengthens your role without adding to your workload."]),
    ("My clients have already saved for college. Do they still need this?",
     ["Saving is only half the equation; strategic spending matters just as much. Academic success doesn't automatically translate into career clarity or the best educational investment."]),
    ("Isn't education funding already part of my role?",
     ["You manage the wealth plan. Pathfinders adds specialized expertise in career exploration, educational fit and Return on Education (ROE), so together your clients get a more complete strategy."]),
]

# --------------------------------------------------------------------------- page config
POST_PAGES = json.loads((ROOT_DIR / "src" / "data" / "post_pages.json").read_text(encoding="utf-8"))
CATEGORY_PAGES = json.loads((ROOT_DIR / "src" / "data" / "categories.json").read_text(encoding="utf-8"))
LOCATIONS = json.loads((ROOT_DIR / "src" / "data" / "locations.json").read_text(encoding="utf-8"))

PAGES = [
    dict(src="index.html", out="index.html", path="/", nav="home",
         title="Education Investment Advisors | Career First. College Second. | Pathfinders",
         desc="Best college admissions consultants guiding high school students and parents in career fit, college choice, and financial strategy. Get started today!",
         og=LOGO_STACK, name="Home"),
    dict(src="educators.html", out="educators/index.html", path="/educators/", nav="educators",
         title="College Planning Support for School Counselors | Pathfinders",
         desc="Refer families to an expert college advisor — and free yourself to focus where you're needed most. See how Pathfinders supports school counselors.",
         og=WP + "2025/01/iStock-488580160-modified-392d6dff-f811-4327-91dc-fea3f0286496.jpg", name="Educators"),
    dict(src="financial-planners.html", out="financial-planners/index.html", path="/financial-planners/", nav="planners",
         title="College Financial Aid Guidance for Families - Pathfinders",
         desc="Help clients optimize college portfolios with expert financial aid planning. Free up 10-30% of funds through strategic college selection. Get started now.",
         og=WP + "2025/01/iStock-488580160-modified-392d6dff-f811-4327-91dc-fea3f0286496.jpg", name="Financial Planners"),
    dict(src="workshops.html", out="workshops/index.html", path="/workshops/", nav="workshops",
         title="Workshops - Pathfinders Advisors",
         desc="Most families begin by asking: \"What college should my student attend?\"At Pathfinders, we ask a better question: \"What career will help your student thrive?\"",
         og=WP + "2026/07/Webinars-image.jpg-1024x683.jpeg", name="Workshops"),
    dict(src="resources.html", out="resources/index.html", path="/resources/", nav="resources",
         title="Resources & Insights for College Planning - Pathfinders Advisors",
         desc="Navigate the complex world of college admissions with Pathfinders. Discover expert guidance and strategic insights to maximize your education investment. Explore now!",
         og=LOGO_STACK, name="Knowledge Base"),
    dict(src="about.html", out="about/index.html", path="/about/", nav="about",
         title="About Susan Cornish — College Planning Expert | Pathfinders",
         desc="Meet Susan Cornish — college planning expert with 19+ yrs experience. We've helped 1,500+ students find their best-fit school & career path.",
         og=WP + "2025/01/iStock-488580160-modified-392d6dff-f811-4327-91dc-fea3f0286496.jpg", name="About Us"),
    dict(src="contact-us.html", out="contact-us/index.html", path="/contact-us/", nav="contact",
         title="Contact Pathfinders Advisors: Start Your College Planning Journey",
         desc="Get in touch with Pathfinders Advisors for expert guidance. Visit our contact page to connect with our team today and start your journey to success.",
         og=WP + "2026/10/pf-advising-session-qr.png", name="Contact"),
    dict(src="faq.html", out="faq/index.html", path="/faq/", nav="",
         title="Frequently Asked Questions - Pathfinders Advisors",
         desc="Get answers to common questions about college consulting costs, the admissions process, career planning, and how Pathfinders Advisors supports families.",
         og=LOGO_STACK, name="Frequently Asked Questions"),
    dict(src="testimonials.html", out="testimonials/index.html", path="/testimonials/", nav="",
         title="Testimonials - Pathfinders Advisors",
         desc="Read real stories from families who worked with Pathfinders Advisors to navigate college admissions, save on tuition, and secure scholarships.",
         og=WP + "2020/11/female-student-1.png", name="Testimonials"),
    dict(src="services.html", out="services/index.html", path="/services/", nav="",
         title="Services - Pathfinders Advisors",
         desc="Navigate financial complexities with Pathfinder Advisors. Our services empower families with informed financial planning. Learn more today.",
         og=LOGO_STACK, name="Services"),
    dict(src="html-sitemap.html", out="html-sitemap/index.html", path="/html-sitemap/", nav="",
         title="HTML Sitemap - Pathfinders Advisors",
         desc="Testimonials Shop Activate Rightwaywebinar Services Members Terms Of Service Login My Profile College Planning Essentials Sat Act Quick Reference Guide",
         og=LOGO_STACK, name="HTML Sitemap"),
    dict(src="privacy-policy.html", out="privacy-policy/index.html", path="/privacy-policy/", nav="",
         title="Privacy Policy - Pathfinders Advisors",
         desc="Learn how Pathfinders Advisors collects, uses, and protects your personal information. Our commitment to privacy and data security is outlined here.",
         og=LOGO_STACK, name="Privacy Policy"),
    dict(src="terms-of-service.html", out="terms-of-service/index.html", path="/terms-of-service/", nav="",
         title="Terms of Service - Pathfinders Advisors",
         desc="Explore Pathfinders Advisors' Terms of Service to understand how we protect your interests. Gain clarity and discover how we prioritize your financial journey today.",
         og=LOGO_STACK, name="Terms of Service"),
    dict(src="susan-cornish.html", out="susan-cornish/index.html", path="/susan-cornish/", nav="about",
         title="About Susan Cornish - College and Career Planning Experts",
         desc="Susan Cornish brings 19 years of corporate experience and over 15 years as an entrepreneur to guide students and families through college planning, career exploration, and finding the right path forward.",
         og=WP + "2025/04/image2.png", name="Susan Cornish", person=("susan-cornish", "Susan Cornish")),
    dict(src="aly-foster.html", out="aly-foster/index.html", path="/aly-foster/", nav="about",
         title="About Aly Foster - College and Career Planning Experts",
         desc="Aly Foster brings a decade of experience helping families navigate personalized college and career planning decisions, finding the right path forward.",
         og=WP + "2025/04/image4.png", name="Aly Foster", person=("aly-foster", "Aly Foster")),
    dict(src="alyssa-rader.html", out="alyssa-rader/index.html", path="/alyssa-rader/", nav="about",
         title="About Alyssa Rader \u2013 College & Career Planning Experts",
         desc="Alyssa Rader understands how hard it can be to choose a direction when you know your strengths but aren't sure where they'll lead. After earning a degree in",
         og=WP + "2026/11/Alyssa-Rader.webp", name="Alyssa Rader", person=("alyssa-rader", "Alyssa Rader")),
    dict(src="amy-wisdom.html", out="amy-wisdom/index.html", path="/amy-wisdom/", nav="about",
         title="About Amy Wisdom \u2013 College & Career Planning Experts",
         desc="Proud mom and dedicated Realtor balancing a full house and a busy career. I\u2019m celebrating two major milestones this year: my daughter is graduating from FSU",
         og=WP + "2026/03/Amy-Wisdom-1024x682.webp", name="Amy Wisdom", person=("amy-wisdom", "Amy Wisdom"), noindex=True, canonical=False),
    dict(src="get-college-right.html", out="get-college-right/index.html", path="/get-college-right/", nav="",
         title='Get College Right - Pathfinders Advisors', desc='Choosing the right major and college can feel overwhelming.With rising costs and confusing admissions systems, it’s no wonder:',
         og=WP + "2023/09/pexels-george-pak-7972481-683x1024.jpg", name='Get College Right'),
    dict(src="sat-act-quick-reference-guide.html", out="sat-act-quick-reference-guide/index.html", path="/sat-act-quick-reference-guide/", nav="",
         title='SAT/ACT Quick Reference Guide - Pathfinders Advisors', desc='Download our free SAT vs ACT quick reference guide with test dates, comparison tables, and prep strategies to help your student pick the right exam.',
         og=WP + "2025/05/Congrats-1024x1024.png", name='SAT/ACT Quick Reference Guide'),
    dict(src="college-application-checklist.html", out="college-application-checklist/index.html", path="/college-application-checklist/", nav="",
         title='College Application Checklist - Pathfinders Advisors', desc='Download our free college application checklist covering essays, deadlines, financial aid, and every step your family needs to stay organized.',
         og=WP + "2025/05/Congrats-1024x1024.png", name='College Application Checklist'),
    dict(src="summer-camp-scholarship.html", out="summer-camp-scholarship/index.html", path="/summer-camp-scholarship/", nav="",
         title='Summer Camp Scholarship - Pathfinders Advisors', desc='Apply for the Pathfinders Advisors summer camp scholarship to help your high school student explore careers and build a strong college profile.',
         og=WP + "2026/01/Image_2025-12-31_at_2.48.17_AM-1024x682.jpeg", name='Summer Camp Scholarship'),
    dict(src="rightwaywebinar.html", out="rightwaywebinar/index.html", path="/rightwaywebinar/", nav="",
         title='Find the Right College & Cost: Webinar by Pathfinders Advisors', desc='Unlock the secrets to affordable college selection with our 30-minute webinar. Discover expert strategies to find the right college for your high schooler. Watch now!',
         og=WP + "2020/10/logo2.png", name='Rightwaywebinar'),
    dict(src="college-planning-locations.html", out="college-planning-locations/index.html", path="/college-planning-locations/", nav="",
         title=LOCATIONS["hub"]["title"], desc=LOCATIONS["hub"]["desc"], og=LOCATIONS["hub"]["og"], name="College Planning Locations"),
] + [
    dict(src="city", city=c, out=c["path"].strip("/") + "/index.html", path=c["path"], nav="",
         title=c["title"], desc=c["desc"], og=c["og"], name=c["h1"])
    for c in LOCATIONS["cities"]
] + [
    dict(src="post", post=x, out=x["slug"] + "/index.html", path=x["path"], nav="resources",
         title=x.get("meta_title") or x["title"], desc=x.get("desc", ""), og=x.get("og") or LOGO_STACK, name=x["title"],
         noindex="noindex" in x.get("robots", ""), canonical=False if not x.get("canonical") else None)
    for x in POST_PAGES
] + [
    dict(src="category", cat=c, out=c["path"].strip("/") + "/index.html", path=c["path"], nav="resources",
         title=c["meta_title"], desc=c["desc"], og=c.get("og") or LOGO_STACK, name=c["name"])
    for c in CATEGORY_PAGES
] + [
    dict(src="404.html", out="404.html", path="/404/", nav="", title="Page not found | Pathfinders Advisors",
         desc="This page could not be found.", og=LOGO_STACK, name="Not found", noindex=True),
]

BUILT_PATHS = {p["path"] for p in PAGES if p["src"] != "404.html"}


def link(path, root):
    """Relative link to a page this site builds, else the page on the live site."""
    return root + path.lstrip("/") if path in BUILT_PATHS else SITE + path


NAV = [
    ("home", "Families", ""),
    ("educators", "Educators", "educators/"),
    ("planners", "Financial Planners", "financial-planners/"),
    ("workshops", "Workshops", "workshops/"),
    ("resources", "Knowledge Base", "resources/"),
    ("about", "About", "about/"),
]

# --------------------------------------------------------------------------- helpers


def upcoming_workshops():
    out = []
    for title, iso, shown in WORKSHOPS:
        start = dt.datetime.fromisoformat(iso)
        if start > NOW:
            out.append((title, iso, shown, start))
    return out


def fmt_date(d):
    return d.strftime("%B %-d, %Y")


def article_url(slug):
    return f"{SITE}/{slug}/"


def initials(name):
    parts = [p for p in re.split(r"\s+", name) if p]
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


# --------------------------------------------------------------------------- renderers


def r_reviews(_arg, ctx):
    cards = []
    for name, text in GOOGLE_REVIEWS:
        cards.append(
            f'<article class="review reveal"><div class="review-head"><span class="avatar" aria-hidden="true">{e(initials(name))}</span>'
            f'<div><div class="review-name">{e(name)}</div><div class="review-source">Posted on Google</div></div></div>'
            f'<p class="clamp">{e(text)}</p></article>')
    return '<div class="reviews">' + "".join(cards) + "</div>"


def r_quote(arg, ctx):
    q = QUOTES[arg]
    return (f'<figure class="featured-quote reveal"><div class="qmark" aria-hidden="true">“</div><div>'
            f'<blockquote><p>{e(q["text"])}</p></blockquote>'
            f'<figcaption class="who">{e(q["name"])}<span>{e(q["meta"])}</span></figcaption></div></figure>')


def r_quotecards(arg, ctx):
    keys = arg.split(",")
    cards = []
    for k in keys:
        q = QUOTES[k]
        cards.append(f'<figure class="review reveal" style="margin:0"><blockquote style="margin:0"><p>{e(q["text"])}</p></blockquote>'
                     f'<figcaption class="review-head" style="margin:16px 0 0"><span class="avatar" aria-hidden="true">{e(initials(q["name"]))}</span>'
                     f'<div><div class="review-name">{e(q["name"])}</div><div class="review-source">{e(q["meta"])}</div></div></figcaption></figure>')
    return '<div class="grid-3 cards-wrap">' + "".join(cards) + "</div>"


def post_card(a, root, searchable=True):
    title, slug, date, img, alt, cats, excerpt = a
    d = dt.date.fromisoformat(date)
    tag = cats[0] if cats else "Blog"
    img = img or LOGO_STACK
    fit = " thumb-logo" if "Pathfinders_stack_RGB" in img else ""
    attrs = ""
    if searchable:
        hay = " ".join([title, excerpt, " ".join(cats), " ".join(ARTICLE_KEYWORDS.get(slug, []))]).lower()
        attrs = f' data-cats="{e("|".join(cats))}" data-search="{e(hay)}"'
    return (f'<a class="post-card reveal" href="{link("/" + slug + "/", root)}"{attrs}>'
            f'<div class="thumb{fit}"><img src="{e(img)}" alt="{e(alt)}" loading="lazy" width="768" height="480"></div>'
            f'<div class="body"><div class="post-meta"><span class="tag">{e(tag)}</span><time datetime="{date}">{fmt_date(d)}</time></div>'
            f'<h3>{e(title)}</h3><p>{e(excerpt)}</p><span class="text-link">Read article</span></div></a>')


def r_articles(arg, ctx):
    """latest:N | planners | topic:<name>:N | all (searchable list for the knowledge base)."""
    root = ctx["root"]
    parts = (arg or "all").split(":")
    if parts[0] == "latest":
        items = ARTICLES[:int(parts[1])]
    elif parts[0] == "planners":
        by_slug = {a[1]: a for a in ARTICLES}
        items = [by_slug[s] for s in PLANNER_ARTICLES if s in by_slug]
    elif parts[0] == "topic":
        items = [a for a in ARTICLES if parts[1] in a[5]][:int(parts[2])]
    else:
        return '<div class="grid-3 cards-wrap">' + "".join(post_card(a, root) for a in ARTICLES) + "</div>"
    return '<div class="grid-3 cards-wrap">' + "".join(post_card(a, root, searchable=False) for a in items) + "</div>"


def r_filters(_arg, ctx):
    chips = ['<button class="chip" type="button" data-filter="all" aria-pressed="true">All articles</button>']
    for c in CATEGORIES:
        chips.append(f'<button class="chip" type="button" data-filter="{e(c)}" aria-pressed="false">{e(c)}</button>')
    return '<div class="filter-bar" role="group" aria-label="Filter articles by topic">' + "".join(chips) + "</div>"


def r_faq(arg, ctx):
    items = []
    faqs = FP_FAQS if arg == "planners" else ([(x["q"], x["a"]) for x in FAQ_PAGE] if arg == "page" else FAQS)
    for i, (q, answer) in enumerate(faqs):
        body = "".join(f"<p>{e(p)}</p>" for p in answer)
        items.append(f'<details{" open" if i == 0 else ""}><summary>{e(q)}</summary><div class="answer">{body}</div></details>')
    return '<div class="faq">' + "".join(items) + "</div>"


def r_workshops(arg, ctx):
    rows = []
    for title, iso, shown, start in upcoming_workshops():
        rows.append(
            f'<article class="event reveal" data-event-start="{iso}">'
            f'<div class="event-date" aria-hidden="true"><span class="m">{start.strftime("%b")}</span><span class="d">{start.day}</span></div>'
            f'<div><h3>{e(title)}<span class="tag next-label" hidden>Next up</span></h3>'
            f'<p><time datetime="{iso}">{start.strftime("%A, %B")} {start.day}, {start.year} · {shown}</time> · Free virtual workshop</p></div>'
            f'<a class="btn btn-sm" href="{WORKSHOP_URL}" target="_blank" rel="noopener">Reserve a seat<span class="sr-only"> for {e(title)}</span></a></article>')
    empty = ('<div class="events-empty card"><h3>New dates are on the way</h3>'
             f'<p class="muted">Our next round of free workshops is being scheduled. <a href="{WORKSHOP_URL}" target="_blank" rel="noopener">Check the workshop page</a> or <a href="{ctx["root"]}contact-us/#book">book a family strategy call</a> in the meantime.</p></div>')
    return '<div><div class="event-list">' + "".join(rows) + "</div>" + empty + "</div>"


def r_guides(arg, ctx):
    cards = []
    for title, img, blurb in GUIDES:
        pic = "" if arg == "noimage" else f'<img src="{img}" alt="{e(title)} preview" loading="lazy" width="600" height="340">'
        cards.append(f'<article class="guide-card reveal">{pic}'
                     f'<div class="body"><span class="tag">Free download</span><h3>{e(title)}</h3><p class="muted" style="margin:8px 0 0;font-size:.98rem">{e(blurb)}</p></div></article>')
    return '<div class="grid-2">' + "".join(cards) + "</div>"


# Where each form posts its data (multipart FormData). Leave empty until the CRM
# webhook exists; an empty endpoint keeps the "not connected yet" review message.
FORM_ENDPOINTS = {"contact": "", "resource": "", "educator": "", "planner": "", "profile": ""}
FORM_NAMES = {"contact": "Website contact", "resource": "Free resource request",
              "educator": "Educator inquiry", "planner": "Financial planner inquiry", "profile": "Team profile inquiry"}

CONSENT = "By submitting this form, I agree to receive email communications from Pathfinders College &amp; Career Advisors related to my inquiry."


def field(name, label, typ="text", required=False, full=False, auto=None, options=None, rows=None):
    req = ' <span class="req" aria-hidden="true">*</span>' if required else ""
    r = " required" if required else ""
    a = f' autocomplete="{auto}"' if auto else ""
    fid = f"f-{name}-{{FORMID}}"
    cls = "field full" if full else "field"
    if options is not None:
        opts = "".join(f'<option value="{e(o)}">{e(o)}</option>' for o in options)
        ctrl = f'<select id="{fid}" name="{name}"{r}><option value="">Select one</option>{opts}</select>'
    elif rows:
        ctrl = f'<textarea id="{fid}" name="{name}" rows="{rows}"{r}></textarea>'
    else:
        ctrl = f'<input id="{fid}" name="{name}" type="{typ}"{a}{r}>'
    return f'<div class="{cls}"><label for="{fid}">{label}{req}</label>{ctrl}</div>'


GRAD_YEARS = [str(y) for y in range(NOW.year, NOW.year + 6)] + ["Other / not sure"]


def r_form(kind, ctx):
    pick = None
    if kind.startswith("resource:"):  # resource form with one guide already chosen
        kind, pick = "resource", int(kind.split(":")[1])
    if kind in ("educator", "planner"):
        fields = [field("full_name", "Full name", required=True, full=True, auto="name"),
                  field("email", "Email", "email", True, auto="email"),
                  field("phone", "Phone number", "tel", auto="tel"),
                  field("organization", "Organization" if kind == "educator" else "Firm / organization", auto="organization"),
                  field("zip", "ZIP code", auto="postal-code")]
        if kind == "educator":
            fields.append(field("support_needed", "What resources or support can we provide to your school?", full=True, rows=4))
        title = "Give every student your guidance and support." if kind == "educator" else "Provide your clients with something they can’t get anywhere else."
        sub = "Tell us a little about your school or district and we’ll be in touch." if kind == "educator" else "Tell us about your practice and we’ll show you how a partnership works."
        btn, success = "Get in touch", "Thank you. Our team will contact you shortly."
    elif kind == "resource":
        fields = [field("first_name", "First name", required=True, auto="given-name"),
                  field("last_name", "Last name", required=True, auto="family-name"),
                  field("email", "Email", "email", True, full=True, auto="email"),
                  field("grad_year", "Student graduation year", options=GRAD_YEARS),
                  field("resource", "Which resource would you like?", required=True, options=[g[0] for g in GUIDES])]
        title, sub = "Send me the free guide", "We’ll email the PDF to you right away."
        btn, success = "Send me the resource", "Thank you. Check your inbox for your guide."
    elif kind == "profile":
        fields = [field("full_name", "Full name", required=True, full=True, auto="name"),
                  field("phone", "Phone number", "tel", auto="tel"),
                  field("email", "Email", "email", True, auto="email"),
                  field("student_name", "Student&rsquo;s name"),
                  field("grad_year", "Graduation year", options=GRAD_YEARS),
                  field("referral", "Who can we thank for your interest in our services?", full=True)]
        title, sub = "Get in touch for all the support you need on your path to a bright future.", "Tell us about your student and we&rsquo;ll be in touch."
        btn, success = "Send", "Thank you. A member of our team will reply soon."
    else:  # contact
        fields = [field("first_name", "First name", required=True, auto="given-name"),
                  field("last_name", "Last name", required=True, auto="family-name"),
                  field("email", "Email", "email", True, auto="email"),
                  field("phone", "Phone", "tel", auto="tel"),
                  field("student_names", "Student first name(s)"),
                  field("grad_year", "Student graduation year", options=GRAD_YEARS),
                  field("message", "How can we help?", full=True, rows=5)]
        title, sub = "Send us a message", "Questions about coaching, the course or workshops? We’ll reply by email."
        btn, success = "Send message", "Thank you. A member of our team will reply soon."
    sms = ""
    if kind == "contact":
        sms = ('<div class="full consent"><label><input type="checkbox" name="sms_service" value="yes"> I agree to receive non-marketing text messages from Pathfinders College &amp; Career Advisors LLC regarding appointments, scheduling, advising services and other communications related to services I have requested. Message frequency may vary. Message and data rates may apply. Reply HELP for help or STOP to opt out.</label></div>'
               '<div class="full consent"><label><input type="checkbox" name="sms_marketing" value="yes"> I agree to receive marketing text messages from Pathfinders College &amp; Career Advisors LLC regarding educational resources, events, programs, services and promotions. Message frequency may vary. Message and data rates may apply. Reply HELP for help or STOP to opt out.</label></div>'
               f'<p class="full consent" style="margin:0">SMS consent is optional and is not a condition of purchasing or receiving services. See our <a href="{link("/privacy-policy/", ctx["root"])}">Privacy Policy</a> and <a href="{link("/terms-of-service/", ctx["root"])}">Terms of Service</a>.</p>')
    body = "".join(fields)
    endpoint = FORM_ENDPOINTS.get(kind, "")
    ep_attr = f' data-endpoint="{e(endpoint)}"' if endpoint else ""
    hidden = (f'<input type="hidden" name="form_name" value="{e(FORM_NAMES[kind])}">'
              f'<input type="hidden" name="page_path" value="{e(ctx["page"]["path"])}">')
    html_out = (f'<form class="form-panel" data-pf-form="{kind}" data-success="{e(success)}"{ep_attr} novalidate>'
                f'{hidden}<h3>{title}</h3><p>{sub}</p><div class="form-grid">{body}'
                f'<div class="hp" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>'
                f'{sms}<p class="full consent" style="margin:0">{CONSENT}</p>'
                f'<div class="full"><button class="btn btn-block" type="submit">{btn}</button></div></div>'
                f'<div class="form-status" role="status" aria-live="polite"></div></form>')
    if pick is not None:
        title = GUIDES[pick][0]
        html_out = html_out.replace(f'<option value="{e(title)}">', f'<option value="{e(title)}" selected>')
    return html_out.replace("{FORMID}", kind)


CTA_COPY = {
    "home": ("Ready? We are too.", "Don’t spend $400,000. There’s a Return on Education.",
             "We get it. Choosing the right college with your student can be daunting. Let us help you put them in the driver’s seat and take the stress off of you.</p><p>Pathfinders isn’t traditional college counseling. We help students discover who they want to become, identify the educational pathway that supports those goals, and build a financial strategy that maximizes Return on Education (ROE)."),
    "planners": ("For advisors who lead with advice", "Make education one of your clients’ smartest investments.",
                 "You’ve helped your clients accumulate wealth. We help ensure one of their largest planned expenditures is aligned with career outcomes, family values and long-term financial goals."),
    "": ("Ready? We are too.", "Put your student in the driver’s seat.",
         "We get it. Choosing the right college with your student can be daunting. Let us help you put them in the driver’s seat and take the stress off of you."),
}
CTA_COPY["educators"] = CTA_COPY[""]
CTA_BUTTON = {"educators": "Schedule time with an expert to learn how we can support your school"}


def r_cta(arg, ctx):
    root = ctx["root"]
    eyebrow, head, para = CTA_COPY.get(arg or "", CTA_COPY[""])
    label = CTA_BUTTON.get(arg or "", "Book a free strategy call")
    return (f'<section class="section-tight"><div class="container"><div class="cta-band reveal">{ROUTE_SVG}'
            f'<div><span class="eyebrow">{eyebrow}</span><h2>{head}</h2>'
            f'<p>{para}</p></div>'
            f'<div class="btn-row"><a class="btn" href="{root}contact-us/#book">{label} {icon("arrow")}</a></div></div></div></section>')


def r_video(arg, ctx):
    caption = {"about": "Meet the Pathfinders team and hear from families who found their path.",
               "workshop": "Watch this 2-minute overview before you reserve your seat."}.get(arg, "")
    headline = ("See how the Career First approach works for families like yours" if arg == "home"
                else "See how Pathfinders has helped families like yours")
    return (f'<figure class="video-card"><video controls preload="metadata" playsinline src="{VIDEO_URL}#t=0.8" '
            f'aria-label="See how Pathfinders has helped families like yours"></video>'
            f'<figcaption><span class="video-badge" aria-hidden="true">{icon("play")}</span><span><strong>{headline}</strong>{e(caption)}</span></figcaption></figure>')


TESTIMONIALS = json.loads((ROOT_DIR / "src" / "data" / "testimonials.json").read_text(encoding="utf-8"))
FAQ_PAGE = json.loads((ROOT_DIR / "src" / "data" / "faq_page.json").read_text(encoding="utf-8"))
OLD_SITEMAP = json.loads((ROOT_DIR / "src" / "data" / "old_sitemap.json").read_text(encoding="utf-8"))
SITE_PAGES = json.loads((ROOT_DIR / "src" / "data" / "site_pages.json").read_text(encoding="utf-8"))


def r_testimonials(_arg, ctx):
    cards = []
    for t in TESTIMONIALS:
        meta = f'<div class="review-source">{e(t["meta"])}</div>' if t.get("meta") else ""
        cards.append(f'<figure class="review reveal"><blockquote style="margin:0"><p>{e(t["text"])}</p></blockquote>'
                     f'<figcaption class="review-head" style="margin:16px 0 0"><span class="avatar" aria-hidden="true">{e(initials(t["name"]))}</span>'
                     f'<div><div class="review-name">{e(t["name"])}</div>{meta}</div></figcaption></figure>')
    return '<div class="reviews">' + "".join(cards) + "</div>"


def r_sitemap(_arg, ctx):
    root = ctx["root"]
    posts = {"/" + a[1] + "/": a[0] for a in ARTICLES}
    names = {p["path"]: p["name"] for p in PAGES if p["src"] != "404.html"}
    entries = {}
    for x in OLD_SITEMAP:
        entries.setdefault(x["path"], x["text"])
    for x in SITE_PAGES:
        entries.setdefault(x["path"], names.get(x["path"], x["title"]))
    for path, name in names.items():
        entries.setdefault(path, name)
    for path, title in posts.items():
        entries.setdefault(path, title)
    page_items = sorted(((t, pth) for pth, t in entries.items() if pth not in posts), key=lambda x: x[0].lower())
    post_items = [(entries[pth], pth) for pth in posts]
    li = lambda items: "".join(f'<li><a href="{link(pth, root)}">{e(t)}</a></li>' for t, pth in items)
    return (f'<div class="sitemap-group"><h2>Pages</h2><ul class="sitemap-list">{li(page_items)}</ul></div>'
            f'<div class="sitemap-group"><h2>Blog Posts</h2><ul class="sitemap-list">{li(post_items)}</ul></div>')


def r_locations(_arg, ctx):
    """Location cards on the hub, in the old page's order with its text."""
    lines = LOCATIONS["hub"]["lines"]
    cards, i = [], 0
    while i < len(lines):
        t, txt = lines[i]
        if t == "h3":
            body = lines[i + 1][1] if i + 1 < len(lines) and lines[i + 1][0] == "p" else ""
            link_text = lines[i + 2][1] if i + 2 < len(lines) and lines[i + 2][0] == "a" else "College planning in " + txt
            slug = next((c["path"] for c in LOCATIONS["cities"] if c["h1"].find(txt.split(",")[0]) >= 0), "")
            cards.append(f'<a class="card audience-card reveal" href="{link(slug, ctx["root"])}">'
                         f'<span class="icon-chip">{icon("map")}</span><h3>{e(txt)}</h3><p>{e(body)}</p>'
                         f'<span class="text-link">{e(link_text)}</span></a>')
            i += 3
            continue
        i += 1
    return '<div class="grid-3 cards-wrap">' + "".join(cards) + "</div>"


def city_body(c, root):
    """A city page, section by section in the old page's order, in the house design."""
    book = f"{root}contact-us/#book"
    out = [f'<section class="page-hero">{ROUTE_SVG}<div class="container">'
           f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol><li><a href="{root}">Home</a></li>'
           f'<li><a href="{root}college-planning-locations/">Locations</a></li><li aria-current="page">{e(c["h1"].split(" College")[0] if c["h1"].startswith(("Columbus", "Cincinnati")) else c["h1"].replace("College & Career Planning in ", ""))}</li></ol></nav>'
           f'<span class="eyebrow">Available virtually</span><h1>{e(c["h1"])}</h1>'
           f'<p class="lead">{e(c["lead"])}</p>'
           f'<div class="btn-row hero-actions"><a class="btn" href="{book}">{e((c.get("hero_links") or ["Book Your Free Strategy Call"])[0])} {icon("arrow")}</a></div>'
           f'</div></section>']
    alt = False
    for sec in c["sections"]:
        kind = sec["kind"]
        eyebrow = f'<span class="eyebrow">{e(sec["eyebrow"].title() if sec["eyebrow"].isupper() else sec["eyebrow"])}</span>' if sec.get("eyebrow") else ""
        head = f'<div class="section-head reveal">{eyebrow}<h2>{e(sec["heading"])}</h2>' + "".join(f"<p>{e(x)}</p>" for x in sec.get("intro", []) if x) + "</div>"
        bg = " bg-cream" if alt else ""
        alt = not alt
        if kind == "text" and sec is c["sections"][-1]:
            label = sec.get("button") or "Book Your Free Strategy Call"
            out.append(f'<section class="section-tight"><div class="container"><div class="cta-band reveal">{ROUTE_SVG}'
                       f'<div><h2>{e(sec["heading"])}</h2>' + "".join(f"<p>{e(x)}</p>" for x in sec.get("intro", [])) +
                       f'</div><div class="btn-row"><a class="btn" href="{book}">{e(label)} {icon("arrow")}</a></div></div></div></section>')
            continue
        if kind == "text":
            btn = f'<a class="btn btn-outline" href="{book}">{e(sec["button"])}</a>' if sec.get("button") else ""
            out.append(f'<section class="section{bg}"><div class="container container-narrow">{head}{btn}</div></section>')
            continue
        if kind in ("cards", "colleges"):
            cards = []
            for it in sec["items"]:
                more = "".join(f'<p class="muted" style="margin:8px 0 0">{e(x)}</p>' for x in it.get("more", []))
                if kind == "colleges" and it["title"].lower().startswith("find the right"):
                    label = sec.get("button") or "Schedule Your Free Call"
                    cards.append(f'<div class="card reveal city-cta-card"><h3>{e(it["title"])}</h3><p>{e(it["text"])}</p>{more}'
                                 f'<a class="btn btn-sm" href="{book}">{e(label)}</a></div>')
                    continue
                chip = f'<span class="icon-chip">{icon("school" if kind == "colleges" else "check")}</span>'
                cards.append(f'<div class="card reveal">{chip}<h3>{e(it["title"])}</h3><p class="muted" style="margin:0">{e(it["text"])}</p>{more}</div>')
            out.append(f'<section class="section{bg}"><div class="container">{head}<div class="grid-3 cards-wrap">{"".join(cards)}</div></div></section>')
            continue
        if kind == "quotes":
            qs = []
            for q in sec["items"]:
                who = e(q["by"]) + (f'<span class="review-source" style="display:block">{e(q["where"])}</span>' if q.get("where") else "")
                qs.append(f'<figure class="review reveal" style="margin:0"><div class="stars" aria-label="5 out of 5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>'
                          f'<blockquote style="margin:0"><p>{e(q["text"])}</p></blockquote>'
                          f'<figcaption class="review-name" style="margin-top:12px">{who}</figcaption></figure>')
            block = f'<section class="section{bg}"><div class="container">{head}<div class="grid-3 cards-wrap">{"".join(qs)}</div>'
            r = sec.get("ready")
            if r:
                block += (f'<div class="card reveal city-ready"><div><h3>{e(r["heading"])}</h3><p class="muted" style="margin:0">{e(r["text"])}</p></div>'
                          f'<a class="btn" href="{book}">{e(r["button"] or "Book Your Free Strategy Call")}</a></div>')
            if sec.get("stats"):
                block += stats_html(sec["stats"])
            out.append(block + "</div></section>")
            continue
        if kind == "stats":
            out.append(f'<section class="section-tight{bg}"><div class="container"><div class="section-head reveal"><h2>{e(sec["heading"])}</h2></div>'
                       f'{stats_html(sec["items"], heading=False)}</div></section>')
            continue
        if kind == "faq":
            items = "".join(f'<details{" open" if i == 0 else ""}><summary>{e(x["q"])}</summary><div class="answer"><p>{e(x["a"])}</p></div></details>'
                            for i, x in enumerate(sec["items"]))
            out.append(f'<section class="section{bg}"><div class="container faq-layout"><div class="sticky reveal">{eyebrow}<h2>{e(sec["heading"])}</h2>'
                       f'<a class="btn btn-outline" href="{book}">Talk to an advisor</a></div><div class="reveal"><div class="faq">{items}</div></div></div></section>')
    return "\n".join(out)


def stats_html(stats, heading=True):
    cells = "".join(f'<div class="stat" role="listitem"><div class="stat-value">{e(x["value"])}</div><div class="stat-label">{e(x["label"])}</div></div>' for x in stats)
    h = '<h3 class="city-stats-title">Pathfinders by the numbers</h3>' if heading else ""
    return f'<div class="city-stats reveal">{h}<div class="stats" role="list">{cells}</div></div>'


LIVE_LINK = re.compile(r'href="(?:https?://(?:www\.)?pathfindersadvisors\.com)?(/[^"#?]*)?([#?][^"]*)?"')


def local_links(body, root):
    """Point links to the old domain (or root-relative ones) at pages this site builds."""
    def fix(m):
        path, rest = m.group(1) or "/", m.group(2) or ""
        if not m.group(0).startswith('href="http') and not m.group(0).startswith('href="/'):
            return m.group(0)
        if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
            path += "/"
        return f'href="{link(path, root)}{rest}"' if path in BUILT_PATHS else m.group(0)
    return LIVE_LINK.sub(fix, body)


def add_heading_ids(body):
    """id on every h2 so the table of contents can link to it."""
    toc, used = [], set()
    def tag(m):
        text = re.sub(r"<[^>]+>", "", m.group(2))
        slug = re.sub(r"[^a-z0-9]+", "-", html.unescape(text).lower()).strip("-")[:60] or "section"
        while slug in used:
            slug += "-2"
        used.add(slug)
        toc.append((slug, text))
        return f'<h2{m.group(1)} id="{slug}">{m.group(2)}</h2>'
    return re.sub(r"<h2([^>]*)>(.*?)</h2>", tag, body, flags=re.S), toc


def post_body(x, root):
    cats = x.get("categories") or []
    cat_links = " ".join(f'<a class="tag" href="{link("/category/" + c["slug"] + "/", root)}">{e(c["name"])}</a>' for c in cats)
    d = dt.date.fromisoformat(x["date"])
    who = f' &middot; By {e(x["author"])}' if x.get("author") else ""
    body, toc = add_heading_ids(local_links(x["body"], root))
    toc_html = ""
    if len(toc) >= 3:
        toc_html = ('<nav class="post-toc" aria-label="Table of contents"><h2>Table of Contents</h2><ol>'
                    + "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in toc) + "</ol></nav>")
    img = x.get("og") or ""
    hero_img = ""
    if img and "Pathfinders_stack_RGB" not in img and "logo" not in img.lower():
        hero_img = f'<figure class="post-hero-img"><img src="{e(img)}" alt="{e(x.get("og_alt") or x["title"])}" width="1200" height="800"></figure>'
    tags = "".join(f'<li>{e(t)}</li>' for t in x.get("tags", []))
    tags_html = f'<div class="post-tags"><h2>Topics</h2><ul>{tags}</ul></div>' if tags else ""
    mine = {c["slug"] for c in cats} - {"blog", "high-school"} or {c["slug"] for c in cats}
    related = [y for y in POST_PAGES if y["slug"] != x["slug"] and mine & {c["slug"] for c in y.get("categories") or []}][:3]
    if len(related) < 3:
        related += [y for y in POST_PAGES if y["slug"] != x["slug"] and y not in related][:3 - len(related)]
    by_slug = {a[1]: a for a in ARTICLES}
    rel = "".join(post_card(by_slug[y["slug"]], root, searchable=False) for y in related if y["slug"] in by_slug)
    title = x.get("h1") or x["title"]
    empty = "" if x["body"].strip() else '<p class="muted">This post has no written content yet. Browse related articles below, or <a href="' + root + 'contact-us/#book">book a free strategy call</a>.</p>'
    return (f'<section class="page-hero post-hero">{ROUTE_SVG}<div class="container container-narrow">'
            f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol><li><a href="{root}">Home</a></li><li><a href="{root}resources/">Knowledge Base</a></li><li aria-current="page">{e(x["title"])}</li></ol></nav>'
            f'<div class="post-cats">{cat_links}</div><h1>{e(title)}</h1>'
            f'<p class="post-byline"><time datetime="{x["date"]}">{fmt_date(d)}</time>{who}</p></div></section>'
            f'<article class="section post"><div class="container container-narrow">{hero_img}{toc_html}'
            f'<div class="prose post-body">{body}{empty}</div>{tags_html}</div></article>'
            f'<section class="section bg-cream"><div class="container"><div class="section-head reveal"><span class="eyebrow">Keep reading</span><h2>Related articles</h2></div>'
            f'<div class="grid-3 cards-wrap">{rel}</div></div></section>'
            "{{CTA}}")


def category_body(c, root):
    items = [a for a in ARTICLES if c["slug"] in {k["slug"] for k in next((y.get("categories") or [] for y in POST_PAGES if y["slug"] == a[1]), [])}]
    cards = "".join(post_card(a, root) for a in items)
    desc = f'<p class="lead">{e(c["description"])}</p>' if c.get("description") else ""
    return (f'<section class="page-hero">{ROUTE_SVG}<div class="container">'
            f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol><li><a href="{root}">Home</a></li><li><a href="{root}resources/">Knowledge Base</a></li><li aria-current="page">{e(c["name"])}</li></ol></nav>'
            f'<span class="eyebrow">Category</span><h1>{e(c["name"])}</h1>{desc}'
            f'<p class="hero-note">{len(items)} article{"s" if len(items) != 1 else ""}</p></div></section>'
            f'<section class="section"><div class="container"><div class="grid-3 cards-wrap">{cards}</div></div></section>'
            "{{CTA}}")


RENDERERS = {
    "REVIEWS": r_reviews, "QUOTE": r_quote, "QUOTECARDS": r_quotecards, "ARTICLES": r_articles,
    "FILTERS": r_filters, "FAQ": r_faq, "WORKSHOPS": r_workshops, "GUIDES": r_guides, "FORM": r_form,
    "CTA": r_cta, "VIDEO": r_video, "TESTIMONIALS": r_testimonials, "SITEMAP": r_sitemap, "LOCATIONS": r_locations,
}

# --------------------------------------------------------------------------- schema


def org_node():
    return {
        "@type": "Organization", "@id": SITE + "/#organization", "name": ORG_NAME,
        "alternateName": ["Pathfinders Advisors", "Pathfinders", "College Liftoff"],
        "url": SITE + "/",
        "logo": {"@type": "ImageObject", "@id": SITE + "/#logo", "url": LOGO, "width": 1522, "height": 320, "caption": "Pathfinders Advisors"},
        "image": {"@id": SITE + "/#logo"},
        "description": "Education Investment Advisors. We help planning-oriented families make smarter education investments by discovering the right career before choosing the right educational pathway.",
        "slogan": "Career First. College Second.",
        "foundingDate": "2009",
        "founder": {"@type": "Person", "@id": SITE + "/about/#aaron-greene", "name": "Aaron Greene"},
        "areaServed": {"@type": "Country", "name": "United States"},
        "knowsAbout": ["Return on Education (ROE)", "Education investment planning", "College admissions", "Career exploration for high school students", "College planning", "Financial aid", "FAFSA", "CSS Profile", "Merit scholarships", "College application essays", "SAT", "ACT", "Education return on investment"],
        "sameAs": list(SOCIAL.values()),
    }


def website_node():
    return {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Pathfinders Advisors",
            "alternateName": ORG_NAME, "publisher": {"@id": SITE + "/#organization"}, "inLanguage": "en-US"}


def webpage_node(p, typ="WebPage"):
    url = SITE + p["path"]
    node = {"@type": typ, "@id": url + "#webpage", "url": url, "name": p["title"], "description": p["desc"],
            "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#organization"}, "inLanguage": "en-US",
            "primaryImageOfPage": {"@type": "ImageObject", "url": p["og"]}}
    if p["path"] != "/":
        node["breadcrumb"] = {"@id": url + "#breadcrumb"}
    return node


def breadcrumb_node(p):
    url = SITE + p["path"]
    return {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": p["name"], "item": url}]}


def faq_node(p, faqs=None):
    return {"@type": "FAQPage", "@id": SITE + p["path"] + "#faq", "isPartOf": {"@id": SITE + p["path"] + "#webpage"},
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": " ".join(a)}} for q, a in (faqs or FAQS)]}


def person(pid, name, job, desc, img, extra=None):
    n = {"@type": "Person", "@id": SITE + "/about/#" + pid, "name": name, "jobTitle": job, "description": desc,
         "image": img, "worksFor": {"@id": SITE + "/#organization"}, "url": SITE + "/about/"}
    if not job:
        n.pop("jobTitle")
    if extra:
        n.update(extra)
    return n


def event_nodes():
    out = []
    for title, iso, shown, start in upcoming_workshops():
        end = start + dt.timedelta(hours=1)
        out.append({
            "@type": "EducationEvent", "@id": SITE + "/workshops/#" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") + "-" + start.strftime("%Y%m%d"),
            "name": f"{title} | Free Virtual Workshop for Families",
            "description": "A free virtual workshop for parents of high school students on career-first college planning: choosing a career direction, the right educational pathway and a strategy to fund it.",
            "startDate": iso, "endDate": end.isoformat(),
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "location": {"@type": "VirtualLocation", "url": WORKSHOP_URL},
            "image": [WP + "2026/07/Webinars-image.jpg-1024x683.jpeg"],
            "organizer": {"@id": SITE + "/#organization"},
            "performer": {"@id": SITE + "/about/#aaron-greene"},
            "isAccessibleForFree": True,
            "audience": {"@type": "Audience", "audienceType": "Parents of high school students"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": WORKSHOP_URL, "validFrom": "2026-07-01T00:00:00-04:00"},
        })
    return out


def service_node(sid, name, desc, audience, stype):
    return {"@type": "Service", "@id": SITE + sid, "name": name, "serviceType": stype, "description": desc,
            "provider": {"@id": SITE + "/#organization"}, "areaServed": {"@type": "Country", "name": "United States"},
            "audience": {"@type": "Audience", "audienceType": audience}}


def schema_for(p):
    g = [org_node(), website_node()]
    key = p["src"]
    if key == "index.html":
        g.append(webpage_node(p))
        svc = service_node("/#college-career-advising", "College & Career Advising",
                           "1:1 virtual coaching for high school students and parents: career discovery, college selection, essays and applications, timeline management and financial aid strategy.",
                           "Parents of high school students and students in grades 9 to 12", "College admissions and career planning consulting")
        svc["hasOfferCatalog"] = {"@type": "OfferCatalog", "name": "Pathfinders services", "itemListElement": [
            {"@type": "Offer", "price": "0", "priceCurrency": "USD", "itemOffered": {"@type": "Service", "name": "Complimentary Family Strategy Call"}},
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "1:1 Virtual College & Career Coaching"}},
            {"@type": "Offer", "itemOffered": {"@type": "Course", "name": "The Pathfinders College & Career Planning Course", "provider": {"@id": SITE + "/#organization"}}},
            {"@type": "Offer", "price": "0", "priceCurrency": "USD", "itemOffered": {"@type": "Service", "name": "Free Virtual College & Career Planning Workshops"}},
        ]}
        g += [svc, faq_node(p)]
    elif key == "educators.html":
        g += [webpage_node(p), breadcrumb_node(p),
              service_node("/educators/#service", "College & Career Planning Support for School Counselors",
                           "Personalized career discovery and college planning for high school students, so counselors with large caseloads can focus where they make the most impact.",
                           "High school counselors and educators", "College and career readiness support")]
    elif key == "financial-planners.html":
        g += [webpage_node(p), breadcrumb_node(p),
              service_node("/financial-planners/#service", "College Planning Partnership for Financial Planners",
                           "A wealth-protection and education planning partner for financial advisors: career-first college selection and financial aid strategy that helps client families invest education dollars with discipline, reduce unnecessary student debt and maximize Return on Education (ROE).",
                           "Financial planners and wealth advisors", "College financial aid planning"),
              faq_node(p, FP_FAQS)]
    elif key == "workshops.html":
        g += [webpage_node(p), breadcrumb_node(p)] + event_nodes()
    elif key == "resources.html":
        page = webpage_node(p, "CollectionPage")
        page["mainEntity"] = {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": article_url(a[1]), "name": a[0]} for i, a in enumerate(ARTICLES)]}
        g += [page, breadcrumb_node(p)]
    elif key == "about.html":
        page = webpage_node(p, "AboutPage")
        g += [page, breadcrumb_node(p),
              person("aaron-greene", "Aaron Greene", "Founder & Lead Advisor",
                     "College planning advisor with 16 years of experience and a degree in mechanical engineering. Creator of the Pathfinders Career-First methodology.",
                     WP + "2025/04/image3.png", {"knowsAbout": ["College planning", "Career exploration", "Financial aid strategy"]}),
              person("susan-cornish", "Susan Cornish", None,
                     "19 years in corporate America, a degree in economics and more than 15 years as an entrepreneur. Helps families tackle college and career planning with no regrets.",
                     WP + "2025/04/image2.png"),
              person("aly-foster", "Aly Foster", None,
                     "Degree in business administration and more than a decade of experience guiding families to personalized decisions.",
                     WP + "2025/04/image4.png"),
              {"@type": "Course", "@id": SITE + "/about/#course", "name": "The Pathfinders College & Career Planning Course",
               "description": "A self-paced, online course that supports college applicants through every phase of finding a career and applying to the most suitable college.",
               "provider": {"@id": SITE + "/#organization"}, "inLanguage": "en-US"}]
    elif key == "contact-us.html":
        g += [webpage_node(p, "ContactPage"), breadcrumb_node(p)]
    elif key == "city":
        c = p["city"]
        place = c["h1"].replace("College & Career Planning in ", "").split(" College")[0]
        svc = service_node(p["path"] + "#service", "College & Career Planning in " + place, p["desc"],
                           "Parents of high school students and students in grades 9 to 12", "College admissions and career planning consulting")
        svc["areaServed"] = {"@type": "City", "name": place}
        faq = next((x for x in c["sections"] if x["kind"] == "faq"), None)
        g += [webpage_node(p), breadcrumb_node(p), svc]
        if faq:
            g.append({"@type": "FAQPage", "@id": SITE + p["path"] + "#faq", "isPartOf": {"@id": SITE + p["path"] + "#webpage"},
                      "mainEntity": [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in faq["items"]]})
    elif key == "faq.html":
        g += [webpage_node(p, "FAQPage"), breadcrumb_node(p)]
        g[-2]["mainEntity"] = [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": " ".join(x["a"])}} for x in FAQ_PAGE]
    elif p.get("person"):
        pid, pname = p["person"]
        page = webpage_node(p, "ProfilePage")
        page["mainEntity"] = {"@id": SITE + "/about/#" + pid}
        g += [page, breadcrumb_node(p), person(pid, pname, None, p["desc"], p["og"])]
    elif key == "post":
        x = p["post"]
        g += [webpage_node(p), breadcrumb_node(p), {
            "@type": "BlogPosting", "@id": SITE + p["path"] + "#article", "headline": x["title"],
            "description": p["desc"], "image": p["og"], "datePublished": x.get("published") or x["date"],
            "dateModified": x.get("modified_time") or x.get("published") or x["date"],
            "author": {"@type": "Person", "name": x.get("author") or ORG_NAME},
            "publisher": {"@id": SITE + "/#organization"}, "mainEntityOfPage": {"@id": SITE + p["path"] + "#webpage"},
            "articleSection": x.get("section") or "", "keywords": ", ".join(x.get("tags", [])), "inLanguage": "en-US"}]
    elif key == "category":
        g += [webpage_node(p, "CollectionPage"), breadcrumb_node(p)]
    elif key != "404.html":
        g += [webpage_node(p), breadcrumb_node(p)]
    else:
        g.append(webpage_node(p))
    data = {"@context": "https://schema.org", "@graph": g}
    return json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")


# --------------------------------------------------------------------------- layout


def announce_bar(root):
    items = []
    for title, iso, shown, start in upcoming_workshops():
        items.append(f'<template data-announce-item="{iso}">Free virtual workshop: <strong>{e(title)}</strong>, {start.strftime("%a %b")} {start.day} at {shown}. '
                     f'<a href="{root}workshops/">Reserve a seat</a></template>')
    first = upcoming_workshops()
    if first:
        t, iso, shown, start = first[0]
        text = f'Free virtual workshop: <strong>{e(t)}</strong>, {start.strftime("%a %b")} {start.day} at {shown}. <a href="{root}workshops/">Reserve a seat</a>'
    else:
        text = f'Free virtual workshops for families. <a href="{root}workshops/">See upcoming dates</a>'
    return (f'<div class="utility-bar"><div class="container"><p class="utility-announce" style="margin:0"><span class="dot" aria-hidden="true"></span>'
            f'<span data-announce data-fallback="{root}workshops/">{text}</span></p>{"".join(items)}'
            f'<nav class="utility-links" aria-label="Course account"><a href="{SITE}/log-in/">Course login</a><a href="{SITE}/register/">Register</a></nav></div></div>')


def header(p, root):
    links = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == p["nav"] else ""
        links.append(f'<li><a href="{root}{href}"{cur}>{label}</a></li>')
    cur_c = ' aria-current="page"' if p["nav"] == "contact" else ""
    links.append(f'<li class="desktop-hide"><a href="{root}contact-us/"{cur_c}>Contact</a></li>')
    mobile = (f'<li class="mobile-only"><a class="btn" href="{root}contact-us/#book">Book a free strategy call</a></li>'
              f'<li class="mobile-only nav-sub"><a href="{SITE}/log-in/">Course login</a></li>'
              f'<li class="mobile-only"><a href="{SITE}/register/" style="font-size:.95rem;color:var(--muted)">Register for the course</a></li>')
    return (announce_bar(root) +
            f'<header class="site-header"><div class="container header-inner">'
            f'<a class="brand" href="{root}" aria-label="Pathfinders Advisors home"><img src="{LOGO_300}" srcset="{LOGO_300} 300w, {LOGO_600} 600w" sizes="200px" width="300" height="63" alt="Pathfinders College &amp; Career Advisors"></a>'
            f'<nav class="main-nav" id="main-nav" aria-label="Main"><button class="nav-close" type="button" aria-label="Close menu">{icon("close")}</button><ul>{"".join(links)}{mobile}</ul></nav>'
            f'<div class="header-cta"><a class="btn btn-sm" href="{root}contact-us/#book">Book a free call</a>'
            f'<button class="nav-toggle" type="button" aria-controls="main-nav" aria-expanded="false" aria-label="Open menu">{icon("menu")}</button></div>'
            f'</div></header><div class="nav-backdrop" aria-hidden="true"></div>')


def footer(root):
    soc = "".join(f'<a href="{u}" target="_blank" rel="noopener" aria-label="Pathfinders on {k.capitalize() if k != "youtube" else "YouTube"}"><svg viewBox="0 0 24 24" aria-hidden="true">{SOCIAL_ICONS[k]}</svg></a>' for k, u in SOCIAL.items())
    return (f'<footer class="site-footer"><div class="container"><div class="footer-grid">'
            f'<div class="footer-brand"><img src="{LOGO_600}" width="600" height="126" alt="Pathfinders College &amp; Career Advisors" loading="lazy">'
            f'<p class="tagline">Career First. College Second.</p><p>Education investment advisors helping families across the United States plan the right career, college and funding path since 2009.</p><p>Join the Career First College Second movement.</p>'
            f'<div class="socials">{soc}</div></div>'
            f'<div><h2>Who we help</h2><ul><li><a href="{root}">Families &amp; students</a></li><li><a href="{root}educators/">School counselors &amp; educators</a></li><li><a href="{root}financial-planners/">Financial planners</a></li></ul></div>'
            f'<div><h2>Learn</h2><ul><li><a href="{root}workshops/">Free workshops</a></li><li><a href="{root}resources/">Knowledge base</a></li><li><a href="{root}#free-guides">Free guides</a></li><li><a href="{SITE}/log-in/">Course login</a></li></ul></div>'
            f'<div><h2>Company</h2><ul><li><a href="{root}about/">About us</a></li><li><a href="{root}contact-us/">Contact</a></li><li><a href="{root}contact-us/#book">Book a strategy call</a></li></ul></div>'
            f'<p class="footer-line">Career First. College Second. | Education Investment Advisors</p>'
            f'</div><div class="footer-bottom"><p style="margin:0">&copy; <span data-year>{NOW.year}</span> Pathfinders College &amp; Career Advisors LLC. All rights reserved.</p>'
            f'<nav aria-label="Legal"><a href="{link("/privacy-policy/", root)}">Privacy Policy</a><a href="{link("/terms-of-service/", root)}">Terms of Service</a><a href="{link("/html-sitemap/", root)}">Sitemap</a></nav></div></div></footer>'
            f'<div class="mobile-cta"><a class="btn" href="{root}contact-us/#book">Book a free strategy call</a></div>')


def layout(p, body, root):
    canonical = SITE + p["path"] if p["src"] != "404.html" else SITE + "/"
    canon_tag = "" if p.get("canonical") is False else f'<link rel="canonical" href="{canonical}">'
    if not LIVE:
        robots = "noindex, nofollow"
    elif p.get("noindex"):
        robots = "noindex, follow"  # as on the old site (amy-wisdom)
    else:
        robots = "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
    return f"""<!doctype html>
<html lang="en-US" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(p["title"])}</title>
<meta name="description" content="{e(p["desc"])}">
<meta name="robots" content="{robots}">
{canon_tag}
<meta property="og:locale" content="en_US">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pathfinders Advisors">
<meta property="og:title" content="{e(p["title"])}">
<meta property="og:description" content="{e(p["desc"])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{p["og"]}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#003D51">
<link rel="icon" href="{WP}2025/01/cropped-Pathfinders_hor_RGB-32x32.png" sizes="32x32">
<link rel="icon" href="{WP}2025/01/cropped-Pathfinders_hor_RGB-192x192.png" sizes="192x192">
<link rel="apple-touch-icon" href="{WP}2025/01/cropped-Pathfinders_hor_RGB-180x180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lexend+Deca:wght@300;400;500;600;700;800&display=swap">
<link rel="stylesheet" href="{root}assets/css/style.css?v={VERSION}">
<script type="application/ld+json">
{schema_for(p)}
</script>
</head>
<body class="page-{p["nav"] or "404"}">
<a class="skip-link" href="#main">Skip to content</a>
{header(p, root)}
<main id="main">
{body}
</main>
{footer(root)}
<script src="{root}assets/js/main.js?v={VERSION}" defer></script>
</body>
</html>
"""


# Trademark mark after every visible "Return on Education" and "ROE". Only text
# between tags is touched, so attributes, schema and meta stay plain. Swap the
# <sup> for the approved trademark graphic here once it arrives.
TM = '<sup class="tm">&trade;</sup>'
ROE_TEXT = re.compile(r"\b(Return on Education|ROE)\b")


def mark_roe(markup):
    parts = re.split(r"(<[^>]+>)", markup)
    for i in range(0, len(parts), 2):
        parts[i] = ROE_TEXT.sub(lambda m: m.group(1) + TM, parts[i])
    return "".join(parts)


UPLOAD_ATTR = re.compile(r'((?:src|srcset|href|poster)=")' + re.escape(WP) + r'([^"]*)"')


def local_uploads(page, root):
    """Serve uploads this repo holds from its own wp-content/ (same paths as the old site).
    Meta tags and structured data keep the absolute URL, which stays valid on the live domain."""
    def fix(m):
        path = m.group(2).split("#")[0].split("?")[0]
        if (ROOT_DIR / "wp-content" / "uploads" / path).exists():
            return f'{m.group(1)}{root}wp-content/uploads/{m.group(2)}"'
        return m.group(0)
    page = UPLOAD_ATTR.sub(fix, page)

    def fix_set(m):  # every candidate inside a srcset
        def one(c):
            path = c.group(1)
            return f"{root}wp-content/uploads/{path}" if (ROOT_DIR / "wp-content" / "uploads" / path).exists() else c.group(0)
        return 'srcset="' + re.sub(re.escape(WP) + r"([^\s,\"]+)", one, m.group(1)) + '"'
    return re.sub(r'srcset="([^"]*)"', fix_set, page)


TOKEN = re.compile(r"\{\{([A-Z_]+)(?::([^}]*))?\}\}")


def render_body(text, ctx):
    def rep(m):
        name, arg = m.group(1), m.group(2)
        if name == "ROOT":
            return ctx["root"]
        if name == "ICON":
            return icon(arg)
        if name == "ROUTE":
            return ROUTE_SVG
        if name == "SITE":
            return SITE
        if name == "WP":
            return WP
        if name == "BOOK_URL":
            return BOOK_URL
        if name == "WORKSHOP_URL":
            return WORKSHOP_URL
        if name == "ARTICLE_COUNT":
            return str(len(ARTICLES))
        if name in RENDERERS:
            return RENDERERS[name](arg, ctx)
        raise KeyError(f"Unknown token {name}")
    out = TOKEN.sub(rep, text)
    return mark_roe(TOKEN.sub(rep, out))  # second pass for tokens produced by renderers


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ROOT_DIR / "assets", OUT / "assets")
    if (ROOT_DIR / "wp-content").exists():  # uploads copied from the old site (tools/fetch_uploads.py)
        shutil.copytree(ROOT_DIR / "wp-content", OUT / "wp-content")
    for p in PAGES:
        depth = p["out"].count("/")
        root = "../" * depth if depth else "./"
        if p["src"] == "404.html":
            root = "/"  # 404 is served at any depth, so its links must be absolute
        if p["src"] == "city":
            text = city_body(p["city"], root)
        elif p["src"] == "post":
            text = post_body(p["post"], root)
        elif p["src"] == "category":
            text = category_body(p["cat"], root)
        else:
            text = (SRC / p["src"]).read_text(encoding="utf-8")
        body = render_body(text, {"root": root, "page": p})
        dest = OUT / p["out"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(local_uploads(layout(p, body, root), root), encoding="utf-8")
        print("built", p["out"])
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    robots = "User-agent: *\nDisallow: /\n" if not LIVE else f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots, encoding="utf-8")
    if LIVE:
        urls = "".join(f"<url><loc>{SITE}{p['path']}</loc></url>" for p in PAGES if not p.get("noindex"))
        (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf-8")
    print("done:", "LIVE build" if LIVE else "review build (noindex)")


if __name__ == "__main__":
    build()
