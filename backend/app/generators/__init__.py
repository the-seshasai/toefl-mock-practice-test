from app.generators.base import TaskGenerator
from app.generators.build_sentence import BuildSentenceGenerator
from app.generators.complete_words import CompleteWordsGenerator
from app.generators.listening import (
    AcademicTalkGenerator,
    AnnouncementGenerator,
    ConversationGenerator,
    ListenReplyGenerator,
)
from app.generators.read_academic import ReadAcademicGenerator
from app.generators.read_daily_life import ReadDailyLifeGenerator
from app.generators.speaking import InterviewGenerator, RepeatGenerator
from app.generators.write_discussion import WriteDiscussionGenerator
from app.generators.write_email import WriteEmailGenerator
from app.spec import TaskType

REGISTRY: dict[TaskType, TaskGenerator] = {
    TaskType.LISTEN_CHOOSE_RESPONSE: ListenReplyGenerator(),
    TaskType.LISTEN_CONVERSATION: ConversationGenerator(),
    TaskType.LISTEN_ANNOUNCEMENT: AnnouncementGenerator(),
    TaskType.LISTEN_ACADEMIC_TALK: AcademicTalkGenerator(),
    TaskType.LISTEN_AND_REPEAT: RepeatGenerator(),
    TaskType.TAKE_INTERVIEW: InterviewGenerator(),
    TaskType.COMPLETE_THE_WORDS: CompleteWordsGenerator(),
    TaskType.READ_DAILY_LIFE: ReadDailyLifeGenerator(),
    TaskType.READ_ACADEMIC: ReadAcademicGenerator(),
    TaskType.BUILD_A_SENTENCE: BuildSentenceGenerator(),
    TaskType.WRITE_EMAIL: WriteEmailGenerator(),
    TaskType.WRITE_ACADEMIC_DISCUSSION: WriteDiscussionGenerator(),
}
