import os
import argparse
import json
import shortuuid
import random

from tqdm import tqdm

from robin.serve.robin_inference import Robin

# Note: We assuming that the question file passed in is the in the format provided in the CLEVR dataset downloaded from https://cs.stanford.edu/people/jcjohns/clevr/ 
# https://dl.fbaipublicfiles.com/clevr/CLEVR_v1.0.zip
# e.g. CLEVR_v1.0/questions/CLEVR_test_questions.json , which correspond to images in CLEVR_v1.0/images/test
def eval_model(args):
    # To ensure deterministic sampling
    random.seed(args.seed)

    questions_file_path = os.path.expanduser(args.question_file)
    img_folder = os.path.expanduser(args.image_folder)
    answers_file = os.path.expanduser(args.answers_file)
    question_data = [ json.loads(line) for line in open(os.path.expanduser(questions_file_path), "r")]
    questions = question_data[0]["questions"]
    num_samples = args.sample
    question_indices = [ i for i in range(len(questions)) ]

    if num_samples > 0:
        print(f"Randomly sampling {num_samples}/{len(questions)} questions using seed {args.seed}")
        random.shuffle(question_indices)
        question_indices = question_indices[:num_samples]
    else:
        print(f"Doing inference on full set of {len(questions)} questions")

    ans_file = open(answers_file, "w")

    robin = Robin(args.model_path,
                model_base=args.model_base,
                device=args.device,
                conv_mode=args.conv_mode,
                temperature=args.temperature,
                max_new_tokens=128
            )

    for idx in tqdm(question_indices):
        q = questions[idx]
        question_idx = q["question_index"]
        image_filename = q["image_filename"]
        image_path = os.path.join(img_folder, image_filename)
        question_prompt = q["question"]
        answer_id = shortuuid.uuid()

        # Inference
        outputs = robin(image_path, question_prompt)

        ans_file.write(json.dumps({"question_id": question_idx,
                                    "prompt": question_prompt,
                                    "text": outputs,
                                    "answer_id": answer_id,
                                    "model_id": robin.model_name,
                                    "metadata": {}}) + "\n")
        ans_file.flush()

    ans_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="agi-collective/mistral-7b-oh-siglip-so400m-finetune-lora")
    parser.add_argument("--model-base", type=str, default="teknium/OpenHermes-2.5-Mistral-7B")
    parser.add_argument("--image-folder", type=str, default="CLEVR_v1.0/images/test")
    parser.add_argument("--question-file", type=str, default="CLEVR_v1.0/questions/CLEVR_test_questions.json")
    parser.add_argument("--answers-file", type=str, default="answers.jsonl")
    parser.add_argument("--conv-mode", type=str, default="llava_v1")
    parser.add_argument("--num-chunks", type=int, default=1)
    parser.add_argument("--chunk-idx", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=1)
    parser.add_argument("--sample", type=int, default=0, help="Number of questions to sample. If 0 (default), full question set is used.")
    parser.add_argument("--device", type=str, default="cuda", help="Device to use. Default is 'cuda'. For specific GPU, input 'cuda:<device_id>'.")
    parser.add_argument("--seed", type=int, default=1234, help="Random seed, default is 1234.")

    args = parser.parse_args()

    eval_model(args)