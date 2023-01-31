# homo_silicus
Replication code for https://www.john-joseph-horton.com/papers/llm_ask.pdf

Here's a twitter thread on the paper: https://twitter.com/johnjhorton/status/1606364947335741453?s=20&t=Sl-wyNhS3ttHkZKz0Jup3Q

Quite a few people have asked for this code. 
It's still a bit, uh, academic, but I don't want the perfect to be the enemy of the good, so here it is! 

A few notes
- The code for the actual experiments are in /experiments folders 
- You'll need to add you own Open AI key in a .env file for this to run
- You should be able to run averything from a Makefile in /writeup
- When you run experiments, they'll create sqlite databases where the actual experimental data is stored (as JSON)
- If you run into problems, create an issue and I'll try to help you out. 

If you do make use of it, I'd appreciate a citation: 
```
@article{horton2023large,
  title={Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?},
  author={Horton, John J},
  journal={arXiv preprint arXiv:2301.07543},
  year={2023}
}
```

Also, if you have ideas on how one might architect this into a real Python library, get in touch! 
I'm a hobbyist Python programmer and I'm sure ther are much nicer ways we could do all of this. 
