# Session 7 Reference Queries

## A. Shannon Wikipedia
Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.

## B. Tokyo activities and weather
Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one is most appropriate.

## C1. Mom's birthday
My mom's birthday is 15 May 2026. Remember that and create reminders for two weeks before and on the day.

## C2. Mom's birthday
When is mom's birthday?

## D. Asyncio research
Search for "Python asyncio best practices", read the top 3 results, and give me a short numbered list of the advice they agree on.

## E. Single-document index and extract
Index the file crawled_papers/attention.md and tell me what the three key contributions of the Transformer architecture are according to this paper.

## F1. Cross-run document recall
Index every .md file under crawled_papers/. Confirm how many chunks were indexed in total.

## F2. Cross-run document recall
Across the papers I have indexed, what do they say about chain-of-thought reasoning?

## G. Synonym recall
Across these papers, how do they handle the credit assignment problem?

## H. Cross-document synthesis
Compare how the ReAct paper and the Chain-of-Thought paper differ in their treatment of intermediate reasoning.

## I. PG - Semantic recall - shy geeks
How do shy geeks show their teeth? Give a reference to the essay name and date as part of your answer.

<!--  This stresses the semantic vector because it completely avoids the exact keywords "fierce" and "nerds." A normal LLM cannot answer this correctly. Your RAG system must semantically map "shy geeks" to "nerds" and "teeth" to "fierce" to succeed.-->

## J. PG - Semantic recall - Charm Authority
Why is magnetic charm usually just an illusion created by authority? Give a reference to the essay name and date as part of your answer.

<!--  This avoids the exact title words "charisma" and "power." A standard LLM will give generic leadership advice or quote popular psychology. To find this, your RAG system has to semantically map "magnetic charm" to "charisma" and "authority" to "power" to retrieve his argument that we imagine powerful people to be charismatic, not the other way around.-->

## K. PG - Semantic recall - Haters
Why do some individuals develop an obsessive dislike or hatred toward famous people? Give a reference to the essay name and date as part of your answer.

<!--  It avoids the exact word "haters." A normal LLM will give a generic, motivational speech about ignoring cyberbullying. The semantic vector is stressed because it must connect the concepts of "angry internet trolls" and "winning" to retrieve the specific essay where he mathematically compares them to a tax you pay for being successful.-->


## L. PG - Synthesis of a long document
From all essays we have indexed summarize the top 3 tips related to writing. Give references to the essay names as part of your answer.
 
<!-- Systhesis of a long document with 9 chunks-->


## M. PG - Dynamic Multi Essay Synthesis
From all essays we have indexed choose any 2 essays related to startup survival and summarize them. Give references to the essay names as part of your answer.

<!-- Making the system to be dynamic multi-essay synthesis-->