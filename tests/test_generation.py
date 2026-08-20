from app.generation.generator import Generator


def test_generation():

    generator = Generator()

    context = """
    Our company provides employees with 24 days of paid annual leave
    every calendar year.
    """

    question = "How many days of annual leave do employees receive?"

    answer = generator.generate(
        question=question,
        context=context
    )

    print("\nGenerated Answer:")
    print(answer)

    assert answer