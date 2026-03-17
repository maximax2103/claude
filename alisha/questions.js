// 150 questions for Alisha Psychology Bot
// Categories: sleep, emotions, stress, habits_bad, habits_good, social, selfesteem, purpose, physical, work
// Types: scale (1-10), yesno, choice

const QUESTIONS = [
  // ===== SLEEP (1-20) =====
  { id: 1, cat: 'sleep', type: 'scale', text: 'Сколько часов ты обычно спишь? (1 = меньше 5 часов, 10 = 8-9 часов)', dim: 'sleep', pos: true },
  { id: 2, cat: 'sleep', type: 'scale', text: 'Насколько легко тебе засыпать вечером?', dim: 'sleep', pos: true },
  { id: 3, cat: 'sleep', type: 'scale', text: 'Как часто ты просыпаешься ночью? (1 = каждую ночь, 10 = никогда)', dim: 'sleep', pos: true },
  { id: 4, cat: 'sleep', type: 'scale', text: 'Чувствуешь ли ты себя отдохнувшим после сна?', dim: 'sleep', pos: true },
  { id: 5, cat: 'sleep', type: 'yesno', text: 'Ложишься ли ты спать примерно в одно и то же время каждый день?', dim: 'sleep', pos: true },
  { id: 6, cat: 'sleep', type: 'yesno', text: 'Используешь ли ты телефон прямо перед сном?', dim: 'sleep', pos: false },
  { id: 7, cat: 'sleep', type: 'yesno', text: 'Пьёшь ли ты кофе или энергетики после 16:00?', dim: 'sleep', pos: false },
  { id: 8, cat: 'sleep', type: 'scale', text: 'Как бы ты оценил качество своего сна за последнюю неделю?', dim: 'sleep', pos: true },
  { id: 9, cat: 'sleep', type: 'scale', text: 'Бывают ли у тебя тревожные сны или кошмары? (1 = очень часто, 10 = никогда)', dim: 'sleep', pos: true },
  { id: 10, cat: 'sleep', type: 'yesno', text: 'Есть ли у тебя приятный ритуал перед сном (книга, чай, медитация)?', dim: 'sleep', pos: true },
  { id: 11, cat: 'sleep', type: 'yesno', text: 'Высыпаешься ли ты в рабочие или учебные дни?', dim: 'sleep', pos: true },
  { id: 12, cat: 'sleep', type: 'scale', text: 'Насколько часто ты откладываешь сон ("ещё 5 минут")? (1 = постоянно, 10 = никогда)', dim: 'sleep', pos: true },
  { id: 13, cat: 'sleep', type: 'yesno', text: 'Просыпаешься ли ты иногда самостоятельно без будильника, отдохнувшим?', dim: 'sleep', pos: true },
  { id: 14, cat: 'sleep', type: 'scale', text: 'Чувствуешь ли ты сонливость в середине дня? (1 = постоянно сплю на ходу, 10 = бодр весь день)', dim: 'sleep', pos: true },
  { id: 15, cat: 'sleep', type: 'yesno', text: 'Ты спишь в тёмной и тихой комнате?', dim: 'sleep', pos: true },
  { id: 16, cat: 'sleep', type: 'choice', text: 'Когда ты последний раз по-настоящему хорошо выспался?', options: ['Сегодня', 'На этой неделе', 'Несколько недель назад', 'Уже не помню...'], scores: [10, 7, 4, 1], dim: 'sleep' },
  { id: 17, cat: 'sleep', type: 'scale', text: 'Когда ты ложишься спать, мешают ли тебе тревожные мысли? (1 = всегда мешают, 10 = засыпаю спокойно)', dim: 'sleep', pos: true },
  { id: 18, cat: 'sleep', type: 'choice', text: 'Сколько раз ты нажимал "отложить" на будильнике сегодня утром?', options: ['Ни разу', '1-2 раза', '3-4 раза', 'Потерял счёт'], scores: [10, 7, 4, 1], dim: 'sleep' },
  { id: 19, cat: 'sleep', type: 'scale', text: 'Влияет ли твоя усталость на настроение и отношения с людьми?', dim: 'sleep', pos: false },
  { id: 20, cat: 'sleep', type: 'yesno', text: 'Замечаешь ли ты разницу в своём самочувствии, когда хорошо высыпаешься?', dim: 'sleep', pos: true },

  // ===== EMOTIONS (21-45) =====
  { id: 21, cat: 'emotions', type: 'scale', text: 'Как ты оцениваешь своё настроение прямо сейчас?', dim: 'emotions', pos: true },
  { id: 22, cat: 'emotions', type: 'scale', text: 'Испытываешь ли ты радость хотя бы раз в день?', dim: 'emotions', pos: true },
  { id: 23, cat: 'emotions', type: 'scale', text: 'Как часто ты чувствуешь тревогу или беспокойство? (1 = постоянно, 10 = очень редко)', dim: 'emotions', pos: true },
  { id: 24, cat: 'emotions', type: 'yesno', text: 'Есть ли в твоей жизни что-то, что тебя по-настоящему вдохновляет?', dim: 'emotions', pos: true },
  { id: 25, cat: 'emotions', type: 'choice', text: 'Когда тебе грустно — что ты обычно делаешь?', options: ['Говорю с кем-то близким', 'Даю себе время прочувствовать', 'Отвлекаюсь на что-то', 'Подавляю и игнорирую'], scores: [9, 10, 6, 2], dim: 'emotions' },
  { id: 26, cat: 'emotions', type: 'scale', text: 'Умеешь ли ты распознавать и называть свои эмоции?', dim: 'emotions', pos: true },
  { id: 27, cat: 'emotions', type: 'scale', text: 'Позволяешь ли ты себе грустить, злиться или бояться без осуждения?', dim: 'emotions', pos: true },
  { id: 28, cat: 'emotions', type: 'scale', text: 'Как часто ты подавляешь свои чувства? (1 = всегда подавляю, 10 = всегда выражаю)', dim: 'emotions', pos: true },
  { id: 29, cat: 'emotions', type: 'scale', text: 'Чувствуешь ли ты себя эмоционально наполненным? (1 = полностью опустошён, 10 = переполнен энергией)', dim: 'emotions', pos: true },
  { id: 30, cat: 'emotions', type: 'scale', text: 'Есть ли у тебя ощущение внутренней пустоты? (1 = постоянное ощущение, 10 = нет совсем)', dim: 'emotions', pos: true },
  { id: 31, cat: 'emotions', type: 'scale', text: 'Испытываешь ли ты чувство вины без явной причины? (1 = часто, 10 = практически никогда)', dim: 'emotions', pos: true },
  { id: 32, cat: 'emotions', type: 'scale', text: 'Умеешь ли ты прощать себя за ошибки?', dim: 'emotions', pos: true },
  { id: 33, cat: 'emotions', type: 'scale', text: 'Чувствуешь ли ты благодарность за что-то в своей жизни прямо сейчас?', dim: 'emotions', pos: true },
  { id: 34, cat: 'emotions', type: 'scale', text: 'Испытываешь ли ты зависть к другим людям? (1 = часто и сильно, 10 = почти никогда)', dim: 'emotions', pos: true },
  { id: 35, cat: 'emotions', type: 'choice', text: 'Как долго у тебя обычно держится плохое настроение?', options: ['Несколько часов', 'День', 'Несколько дней', 'Неделями'], scores: [10, 7, 4, 1], dim: 'emotions' },
  { id: 36, cat: 'emotions', type: 'yesno', text: 'Есть ли у тебя любимые способы улучшить настроение, которые действительно работают?', dim: 'emotions', pos: true },
  { id: 37, cat: 'emotions', type: 'scale', text: 'Боишься ли ты своих негативных эмоций? (1 = очень боюсь, 10 = принимаю их)', dim: 'emotions', pos: true },
  { id: 38, cat: 'emotions', type: 'scale', text: 'В целом — считаешь ли ты себя счастливым человеком?', dim: 'emotions', pos: true },
  { id: 39, cat: 'emotions', type: 'scale', text: 'Испытываешь ли ты апатию — когда ничего не хочется? (1 = постоянно, 10 = никогда)', dim: 'emotions', pos: true },
  { id: 40, cat: 'emotions', type: 'scale', text: 'Умеешь ли ты радоваться маленьким вещам — закату, хорошему кофе, улыбке?', dim: 'emotions', pos: true },
  { id: 41, cat: 'emotions', type: 'scale', text: 'Как часто ты испытываешь раздражение или злость? (1 = очень часто, 10 = очень редко)', dim: 'emotions', pos: true },
  { id: 42, cat: 'emotions', type: 'scale', text: 'Чувствуешь ли ты себя любимым и нужным?', dim: 'emotions', pos: true },
  { id: 43, cat: 'emotions', type: 'choice', text: 'Когда ты последний раз был по-настоящему счастлив?', options: ['Сегодня / вчера', 'На этой неделе', 'В этом месяце', 'Давно...'], scores: [10, 7, 4, 2], dim: 'emotions' },
  { id: 44, cat: 'emotions', type: 'scale', text: 'Испытываешь ли ты страх перед будущим? (1 = очень боюсь, 10 = смотрю с уверенностью)', dim: 'emotions', pos: true },
  { id: 45, cat: 'emotions', type: 'scale', text: 'Умеешь ли ты находить что-то хорошее даже в сложных ситуациях?', dim: 'emotions', pos: true },

  // ===== STRESS (46-65) =====
  { id: 46, cat: 'stress', type: 'scale', text: 'Как ты оцениваешь уровень стресса в своей жизни прямо сейчас? (1 = очень высокий, 10 = минимальный)', dim: 'stress', pos: true },
  { id: 47, cat: 'stress', type: 'yesno', text: 'Есть ли в твоей жизни постоянный источник стресса, который ты не можешь устранить?', dim: 'stress', pos: false },
  { id: 48, cat: 'stress', type: 'scale', text: 'Испытываешь ли ты физические симптомы стресса (головная боль, зажатость, проблемы с ЖКТ)? (1 = часто, 10 = никогда)', dim: 'stress', pos: true },
  { id: 49, cat: 'stress', type: 'scale', text: 'Насколько хорошо ты умеешь справляться со стрессом?', dim: 'stress', pos: true },
  { id: 50, cat: 'stress', type: 'yesno', text: 'Практикуешь ли ты техники расслабления (дыхание, медитация, прогулки)?', dim: 'stress', pos: true },
  { id: 51, cat: 'stress', type: 'scale', text: 'Чувствуешь ли ты напряжение в теле прямо сейчас? (1 = очень сильное, 10 = полностью расслаблен)', dim: 'stress', pos: true },
  { id: 52, cat: 'stress', type: 'scale', text: 'Насколько часто ты перегружаешь себя делами? (1 = всегда, 10 = никогда)', dim: 'stress', pos: true },
  { id: 53, cat: 'stress', type: 'scale', text: 'Умеешь ли ты говорить "нет" людям, когда тебе это нужно?', dim: 'stress', pos: true },
  { id: 54, cat: 'stress', type: 'scale', text: 'Тревожат ли тебя вещи, которые ты не можешь контролировать? (1 = постоянно, 10 = умею отпускать)', dim: 'stress', pos: true },
  { id: 55, cat: 'stress', type: 'yesno', text: 'Бывали ли у тебя когда-либо панические атаки или сильная неконтролируемая тревога?', dim: 'stress', pos: false },
  { id: 56, cat: 'stress', type: 'choice', text: 'Как ты чаще всего справляешься со стрессом?', options: ['Спорт / прогулки', 'Общение с близкими', 'Еда / сериалы / телефон', 'Никак — просто терплю'], scores: [10, 8, 4, 1], dim: 'stress' },
  { id: 57, cat: 'stress', type: 'scale', text: 'Чувствуешь ли ты постоянную спешку или нехватку времени? (1 = постоянно тороплюсь, 10 = всё успеваю)', dim: 'stress', pos: true },
  { id: 58, cat: 'stress', type: 'scale', text: 'Влияет ли твой стресс на отношения с близкими людьми? (1 = разрушает, 10 = не влияет)', dim: 'stress', pos: true },
  { id: 59, cat: 'stress', type: 'yesno', text: 'Есть ли у тебя место (дом, природа, кафе), где ты чувствуешь себя в безопасности и спокойно?', dim: 'stress', pos: true },
  { id: 60, cat: 'stress', type: 'choice', text: 'Как ты относишься к тишине и одиночеству?', options: ['Люблю и ценю', 'Нормально', 'Немного некомфортно', 'Невыносимо'], scores: [10, 7, 4, 1], dim: 'stress' },
  { id: 61, cat: 'stress', type: 'scale', text: 'Как часто ты мысленно возвращаешься к прошлым ошибкам и "прокручиваешь" их? (1 = постоянно, 10 = редко)', dim: 'stress', pos: true },
  { id: 62, cat: 'stress', type: 'scale', text: 'Насколько сильно ты беспокоишься о мнении других людей о тебе? (1 = очень сильно, 10 = мне всё равно)', dim: 'stress', pos: true },
  { id: 63, cat: 'stress', type: 'scale', text: 'Есть ли у тебя ощущение, что ты не успеваешь жить? (1 = постоянное ощущение, 10 = нет)', dim: 'stress', pos: true },
  { id: 64, cat: 'stress', type: 'scale', text: 'Умеешь ли ты полностью отключаться от работы или учёбы после её завершения?', dim: 'stress', pos: true },
  { id: 65, cat: 'stress', type: 'scale', text: 'Приходят ли тебе в голову навязчивые мысли, от которых трудно избавиться? (1 = очень часто, 10 = редко)', dim: 'stress', pos: true },

  // ===== BAD HABITS (66-80) =====
  { id: 66, cat: 'habits_bad', type: 'yesno', text: 'Ты куришь?', dim: 'habits', pos: false },
  { id: 67, cat: 'habits_bad', type: 'choice', text: 'Как часто ты употребляешь алкоголь?', options: ['Никогда / крайне редко', 'По праздникам', 'Несколько раз в месяц', 'Каждую неделю или чаще'], scores: [10, 8, 5, 2], dim: 'habits' },
  { id: 68, cat: 'habits_bad', type: 'scale', text: 'Чувствуешь ли ты зависимость от социальных сетей? (1 = не могу без них, 10 = они не управляют мной)', dim: 'habits', pos: true },
  { id: 69, cat: 'habits_bad', type: 'choice', text: 'Сколько часов в день ты проводишь за телефоном?', options: ['До 2 часов', '2–4 часа', '4–6 часов', 'Больше 6 часов'], scores: [10, 7, 4, 1], dim: 'habits' },
  { id: 70, cat: 'habits_bad', type: 'scale', text: 'Насколько часто ты прокрастинируешь — откладываешь важные дела? (1 = постоянно, 10 = почти никогда)', dim: 'habits', pos: true },
  { id: 71, cat: 'habits_bad', type: 'scale', text: 'Переедаешь ли ты в стрессовых ситуациях? (1 = всегда, 10 = никогда)', dim: 'habits', pos: true },
  { id: 72, cat: 'habits_bad', type: 'scale', text: 'Как много сахара, фастфуда или вредной еды в твоём рационе? (1 = очень много, 10 = практически нет)', dim: 'habits', pos: true },
  { id: 73, cat: 'habits_bad', type: 'yesno', text: 'Есть ли у тебя нервные привычки (грызёшь ногти, теребишь волосы, трясёшь ногой)?', dim: 'habits', pos: false },
  { id: 74, cat: 'habits_bad', type: 'scale', text: 'Как часто ты опаздываешь? (1 = всегда опаздываю, 10 = всегда вовремя)', dim: 'habits', pos: true },
  { id: 75, cat: 'habits_bad', type: 'scale', text: 'Сравниваешь ли ты себя с другими в социальных сетях? (1 = постоянно, 10 = никогда)', dim: 'habits', pos: true },
  { id: 76, cat: 'habits_bad', type: 'scale', text: 'Избегаешь ли ты важных дел или разговоров из-за страха? (1 = часто, 10 = никогда)', dim: 'habits', pos: true },
  { id: 77, cat: 'habits_bad', type: 'scale', text: 'Есть ли у тебя привычка жёстко критиковать себя? (1 = постоянно, 10 = никогда)', dim: 'habits', pos: true },
  { id: 78, cat: 'habits_bad', type: 'scale', text: 'Используешь ли ты алкоголь, еду или сериалы как способ убежать от проблем? (1 = часто, 10 = никогда)', dim: 'habits', pos: true },
  { id: 79, cat: 'habits_bad', type: 'scale', text: 'Забываешь ли ты пить воду в течение дня? (1 = почти никогда не пью, 10 = всегда пью достаточно)', dim: 'habits', pos: true },
  { id: 80, cat: 'habits_bad', type: 'choice', text: 'Насколько ты зависишь от кофеина?', options: ['Совсем не пью', 'Иногда, без зависимости', 'Нужна 1–2 чашки в день', 'Без кофе не функционирую'], scores: [10, 8, 5, 2], dim: 'habits' },

  // ===== GOOD HABITS (81-90) =====
  { id: 81, cat: 'habits_good', type: 'scale', text: 'Насколько регулярно ты занимаешься физической активностью? (1 = никогда, 10 = каждый день)', dim: 'habits', pos: true },
  { id: 82, cat: 'habits_good', type: 'scale', text: 'Как часто ты читаешь книги? (1 = никогда, 10 = регулярно)', dim: 'habits', pos: true },
  { id: 83, cat: 'habits_good', type: 'yesno', text: 'Есть ли у тебя утренняя рутина, которой ты придерживаешься?', dim: 'habits', pos: true },
  { id: 84, cat: 'habits_good', type: 'yesno', text: 'Ведёшь ли ты дневник или записи о своих мыслях и чувствах?', dim: 'habits', pos: true },
  { id: 85, cat: 'habits_good', type: 'yesno', text: 'Практикуешь ли ты медитацию или осознанные дыхательные упражнения?', dim: 'habits', pos: true },
  { id: 86, cat: 'habits_good', type: 'yesno', text: 'Есть ли у тебя хобби, которое по-настоящему радует тебя?', dim: 'habits', pos: true },
  { id: 87, cat: 'habits_good', type: 'scale', text: 'Учишься ли ты чему-то новому сейчас? (1 = нет, 10 = активно развиваюсь)', dim: 'habits', pos: true },
  { id: 88, cat: 'habits_good', type: 'scale', text: 'Проводишь ли ты время на свежем воздухе и природе? (1 = редко, 10 = каждый день)', dim: 'habits', pos: true },
  { id: 89, cat: 'habits_good', type: 'scale', text: 'Следишь ли ты за своим питанием, стараясь есть полезную еду?', dim: 'habits', pos: true },
  { id: 90, cat: 'habits_good', type: 'scale', text: 'Ставишь ли ты себе цели и отслеживаешь ли их выполнение?', dim: 'habits', pos: true },

  // ===== SOCIAL / RELATIONSHIPS (91-105) =====
  { id: 91, cat: 'social', type: 'scale', text: 'Есть ли у тебя люди, которым ты полностью доверяешь?', dim: 'social', pos: true },
  { id: 92, cat: 'social', type: 'scale', text: 'Чувствуешь ли ты себя одиноким? (1 = очень одинок, 10 = окружён близкими)', dim: 'social', pos: true },
  { id: 93, cat: 'social', type: 'scale', text: 'Умеешь ли ты открыто говорить о своих чувствах с близкими людьми?', dim: 'social', pos: true },
  { id: 94, cat: 'social', type: 'yesno', text: 'Есть ли в твоей жизни токсичные отношения или люди, которые тебя истощают?', dim: 'social', pos: false },
  { id: 95, cat: 'social', type: 'scale', text: 'Чувствуешь ли ты поддержку со стороны близких?', dim: 'social', pos: true },
  { id: 96, cat: 'social', type: 'scale', text: 'Умеешь ли ты просить о помощи, когда она тебе нужна?', dim: 'social', pos: true },
  { id: 97, cat: 'social', type: 'scale', text: 'Как часто ты чувствуешь себя непонятым? (1 = постоянно, 10 = почти никогда)', dim: 'social', pos: true },
  { id: 98, cat: 'social', type: 'choice', text: 'Как ты сейчас себя чувствуешь в личных отношениях?', options: ['Счастлив и в гармонии', 'Есть сложности, но работаю над ними', 'Хочу отношений, но их нет', 'Сейчас не до отношений'], scores: [10, 6, 5, 7], dim: 'social' },
  { id: 99, cat: 'social', type: 'scale', text: 'Умеешь ли ты устанавливать личные границы в общении?', dim: 'social', pos: true },
  { id: 100, cat: 'social', type: 'scale', text: 'Как часто ты жертвуешь собой ради других в ущерб себе? (1 = всегда, 10 = никогда)', dim: 'social', pos: true },
  { id: 101, cat: 'social', type: 'scale', text: 'Скучаешь ли ты по живому, тёплому общению?', dim: 'social', pos: false },
  { id: 102, cat: 'social', type: 'yesno', text: 'Есть ли у тебя человек, которому ты можешь позвонить в трудную минуту прямо сейчас?', dim: 'social', pos: true },
  { id: 103, cat: 'social', type: 'scale', text: 'Чувствуешь ли ты, что тебя принимают таким, какой ты есть?', dim: 'social', pos: true },
  { id: 104, cat: 'social', type: 'scale', text: 'Умеешь ли ты быстро отпускать обиды? (1 = обижаюсь надолго, 10 = прощаю легко)', dim: 'social', pos: true },
  { id: 105, cat: 'social', type: 'scale', text: 'Выражаешь ли ты благодарность и тепло людям, которые тебе важны?', dim: 'social', pos: true },

  // ===== SELF-ESTEEM (106-120) =====
  { id: 106, cat: 'selfesteem', type: 'scale', text: 'Как ты оцениваешь себя в целом как человека?', dim: 'selfesteem', pos: true },
  { id: 107, cat: 'selfesteem', type: 'scale', text: 'Принимаешь ли ты свои недостатки и слабые стороны?', dim: 'selfesteem', pos: true },
  { id: 108, cat: 'selfesteem', type: 'scale', text: 'Боишься ли ты осуждения или критики от других? (1 = очень боюсь, 10 = не боюсь)', dim: 'selfesteem', pos: true },
  { id: 109, cat: 'selfesteem', type: 'scale', text: 'Умеешь ли ты принимать комплименты без смущения?', dim: 'selfesteem', pos: true },
  { id: 110, cat: 'selfesteem', type: 'scale', text: 'Чувствуешь ли ты себя "достаточно хорошим" — без постоянного стремления доказать что-то?', dim: 'selfesteem', pos: true },
  { id: 111, cat: 'selfesteem', type: 'scale', text: 'Как часто ты сомневаешься в своих решениях и выборах? (1 = всегда сомневаюсь, 10 = доверяю себе)', dim: 'selfesteem', pos: true },
  { id: 112, cat: 'selfesteem', type: 'scale', text: 'Говоришь ли ты с собой так же добро, как говорил бы с лучшим другом?', dim: 'selfesteem', pos: true },
  { id: 113, cat: 'selfesteem', type: 'yesno', text: 'Есть ли в твоей жизни то, чем ты по-настоящему гордишься?', dim: 'selfesteem', pos: true },
  { id: 114, cat: 'selfesteem', type: 'scale', text: 'Позволяешь ли ты себе отдыхать без чувства вины?', dim: 'selfesteem', pos: true },
  { id: 115, cat: 'selfesteem', type: 'scale', text: 'Веришь ли ты, что достоин любви, счастья и хорошего?', dim: 'selfesteem', pos: true },
  { id: 116, cat: 'selfesteem', type: 'scale', text: 'Насколько ты доволен своей внешностью?', dim: 'selfesteem', pos: true },
  { id: 117, cat: 'selfesteem', type: 'scale', text: 'Насколько страх провала мешает тебе пробовать новое? (1 = очень мешает, 10 = не мешает)', dim: 'selfesteem', pos: true },
  { id: 118, cat: 'selfesteem', type: 'scale', text: 'Умеешь ли ты искренне хвалить себя за достижения?', dim: 'selfesteem', pos: true },
  { id: 119, cat: 'selfesteem', type: 'scale', text: 'Как часто ты сравниваешь себя с неким идеальным образом? (1 = постоянно, 10 = никогда)', dim: 'selfesteem', pos: true },
  { id: 120, cat: 'selfesteem', type: 'yesno', text: 'Знаешь ли ты свои сильные стороны и уникальные качества?', dim: 'selfesteem', pos: true },

  // ===== PURPOSE & GOALS (121-135) =====
  { id: 121, cat: 'purpose', type: 'scale', text: 'Есть ли у тебя чёткое понимание того, чего ты хочешь от жизни?', dim: 'purpose', pos: true },
  { id: 122, cat: 'purpose', type: 'scale', text: 'Знаешь ли ты свои главные жизненные ценности?', dim: 'purpose', pos: true },
  { id: 123, cat: 'purpose', type: 'scale', text: 'Чувствуешь ли ты, что движешься в правильном направлении?', dim: 'purpose', pos: true },
  { id: 124, cat: 'purpose', type: 'yesno', text: 'Есть ли у тебя конкретные цели на ближайший год?', dim: 'purpose', pos: true },
  { id: 125, cat: 'purpose', type: 'scale', text: 'Чувствуешь ли ты смысл в том, что делаешь каждый день?', dim: 'purpose', pos: true },
  { id: 126, cat: 'purpose', type: 'scale', text: 'Тревожит ли тебя мысль, что ты теряешь время или живёшь не так? (1 = постоянно, 10 = нет)', dim: 'purpose', pos: true },
  { id: 127, cat: 'purpose', type: 'yesno', text: 'Есть ли у тебя мечта, к которой ты стремишься?', dim: 'purpose', pos: true },
  { id: 128, cat: 'purpose', type: 'scale', text: 'Живёшь ли ты в соответствии со своими истинными ценностями?', dim: 'purpose', pos: true },
  { id: 129, cat: 'purpose', type: 'choice', text: 'Что для тебя сейчас важнее всего?', options: ['Карьера и деньги', 'Отношения и семья', 'Здоровье и саморазвитие', 'Пока не знаю...'], scores: [7, 8, 10, 3], dim: 'purpose' },
  { id: 130, cat: 'purpose', type: 'scale', text: 'Делаешь ли ты хоть что-то каждый день для своих мечт и целей?', dim: 'purpose', pos: true },
  { id: 131, cat: 'purpose', type: 'scale', text: 'Чувствуешь ли ты, что живёшь "чужой" жизнью — по чужим ожиданиям? (1 = полностью чужой, 10 = своей)', dim: 'purpose', pos: true },
  { id: 132, cat: 'purpose', type: 'yesno', text: 'Есть ли что-то в прошлом, о чём ты сильно сожалеешь и никак не можешь отпустить?', dim: 'purpose', pos: false },
  { id: 133, cat: 'purpose', type: 'scale', text: 'Умеешь ли ты расставлять приоритеты и фокусироваться на важном?', dim: 'purpose', pos: true },
  { id: 134, cat: 'purpose', type: 'scale', text: 'Можешь ли ты представить себя счастливым и реализованным через 5 лет?', dim: 'purpose', pos: true },
  { id: 135, cat: 'purpose', type: 'scale', text: 'Делаешь ли ты то, что действительно наполняет тебя изнутри?', dim: 'purpose', pos: true },

  // ===== PHYSICAL HEALTH (136-145) =====
  { id: 136, cat: 'physical', type: 'scale', text: 'Как ты оцениваешь своё физическое здоровье в целом?', dim: 'physical', pos: true },
  { id: 137, cat: 'physical', type: 'scale', text: 'Насколько регулярны твои физические упражнения?', dim: 'physical', pos: true },
  { id: 138, cat: 'physical', type: 'scale', text: 'Как часто ты болеешь? (1 = очень часто, 10 = практически никогда)', dim: 'physical', pos: true },
  { id: 139, cat: 'physical', type: 'yesno', text: 'Есть ли у тебя хронические боли или регулярные недомогания?', dim: 'physical', pos: false },
  { id: 140, cat: 'physical', type: 'scale', text: 'Пьёшь ли ты достаточно воды каждый день?', dim: 'physical', pos: true },
  { id: 141, cat: 'physical', type: 'scale', text: 'Питаешься ли ты регулярно и более-менее сбалансированно?', dim: 'physical', pos: true },
  { id: 142, cat: 'physical', type: 'scale', text: 'Проводишь ли ты время на свежем воздухе каждый день?', dim: 'physical', pos: true },
  { id: 143, cat: 'physical', type: 'scale', text: 'Чувствуешь ли ты энергию и бодрость большую часть дня?', dim: 'physical', pos: true },
  { id: 144, cat: 'physical', type: 'choice', text: 'Когда ты последний раз проходил медицинский осмотр?', options: ['В этом году', 'Год-два назад', 'Несколько лет назад', 'Никогда / не помню'], scores: [10, 6, 3, 1], dim: 'physical' },
  { id: 145, cat: 'physical', type: 'scale', text: 'Умеешь ли ты слушать своё тело и отдыхать, когда оно устало?', dim: 'physical', pos: true },

  // ===== WORK / PRODUCTIVITY (146-150) =====
  { id: 146, cat: 'work', type: 'scale', text: 'Чувствуешь ли ты удовлетворение от своей работы или учёбы?', dim: 'purpose', pos: true },
  { id: 147, cat: 'work', type: 'scale', text: 'Есть ли у тебя баланс между работой / учёбой и личной жизнью?', dim: 'stress', pos: true },
  { id: 148, cat: 'work', type: 'scale', text: 'Испытываешь ли ты эмоциональное выгорание? (1 = постоянно, 10 = никогда)', dim: 'stress', pos: true },
  { id: 149, cat: 'work', type: 'scale', text: 'Умеешь ли ты делегировать задачи и принимать помощь?', dim: 'stress', pos: true },
  { id: 150, cat: 'work', type: 'yesno', text: 'Есть ли у тебя амбиции и профессиональные мечты, которые тебя вдохновляют?', dim: 'purpose', pos: true }
];

// Select N random questions from pool, ensuring category coverage
function selectSessionQuestions(n = 30, previousIds = []) {
  const categories = ['sleep', 'emotions', 'stress', 'habits_bad', 'habits_good', 'social', 'selfesteem', 'purpose', 'physical', 'work'];
  const perCat = { sleep: 4, emotions: 5, stress: 4, habits_bad: 3, habits_good: 2, social: 3, selfesteem: 3, purpose: 3, physical: 2, work: 1 };

  const selected = [];
  const usedIds = new Set(previousIds.slice(-60)); // avoid last 60 asked

  for (const cat of categories) {
    const pool = QUESTIONS.filter(q => q.cat === cat && !usedIds.has(q.id));
    const fallback = QUESTIONS.filter(q => q.cat === cat);
    const source = pool.length >= perCat[cat] ? pool : fallback;
    const shuffled = [...source].sort(() => Math.random() - 0.5);
    const pick = shuffled.slice(0, perCat[cat]);
    pick.forEach(q => { selected.push(q); usedIds.add(q.id); });
  }

  // Shuffle final selection
  return selected.sort(() => Math.random() - 0.5);
}

// Calculate dimension scores from answers
function calculateScores(answers) {
  const dims = { sleep: [], emotions: [], stress: [], habits: [], social: [], selfesteem: [], purpose: [], physical: [] };

  answers.forEach(({ question_id, value_numeric }) => {
    const q = QUESTIONS.find(x => x.id === question_id);
    if (!q || value_numeric == null) return;
    let val = value_numeric;
    // Normalize to 0-100
    const score = (val / 10) * 100;
    if (dims[q.dim]) dims[q.dim].push(score);
  });

  const avg = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 50;

  const scores = {
    sleep: Math.round(avg(dims.sleep)),
    emotions: Math.round(avg(dims.emotions)),
    stress: Math.round(avg(dims.stress)),
    habits: Math.round(avg(dims.habits)),
    social: Math.round(avg(dims.social)),
    selfesteem: Math.round(avg(dims.selfesteem)),
    purpose: Math.round(avg(dims.purpose)),
    physical: Math.round(avg(dims.physical)),
  };

  const weights = { sleep: 1.2, emotions: 1.3, stress: 1.2, habits: 1.0, social: 1.0, selfesteem: 1.3, purpose: 1.0, physical: 1.0 };
  const totalW = Object.values(weights).reduce((a, b) => a + b, 0);
  const wellbeing = Math.round(
    Object.entries(scores).reduce((sum, [k, v]) => sum + v * (weights[k] || 1), 0) / totalW
  );

  return { ...scores, wellbeing };
}

// Alisha advice based on lowest scores
function getAliashaAdvice(scores) {
  const sorted = Object.entries(scores)
    .filter(([k]) => k !== 'wellbeing')
    .sort(([, a], [, b]) => a - b);

  const advice = {
    sleep: ['Твой сон — это фундамент всего. Попробуй ложиться в одно время и убирать телефон за час до сна. 🌙', 'Качество сна напрямую влияет на твоё настроение и силы. Создай себе вечерний ритуал расслабления. ☕'],
    emotions: ['Твои эмоции — это информация, не враги. Попробуй каждый вечер записывать 3 вещи, за которые ты благодарен. ✨', 'Позволь себе чувствовать. Подавленные эмоции не исчезают — они копятся. Поговори с кем-то или напиши в дневник. 💙'],
    stress: ['Ты несёшь много. Попробуй технику 4-7-8: вдох 4 сек, задержка 7, выдох 8. Делай 3 раза в день. 🌬️', 'Стресс — это сигнал, что тебе нужна забота. Что одно маленькое дело ты можешь сделать для себя сегодня? 💆'],
    habits: ['Маленькие привычки меняют жизнь. Выбери одну привычку, которую хочешь изменить, и начни с 5 минут в день. 🌱', 'Ты замечаешь паттерны, которые тебе мешают — это уже большой шаг. Что ты можешь заменить? 🔄'],
    social: ['Связи с людьми питают душу. Напиши сегодня кому-то важному — просто "я думаю о тебе". 💌', 'Одиночество лечится маленькими шагами. Даже короткий разговор может изменить день. 🤝'],
    selfesteem: ['Ты заслуживаешь своей же доброты. Каждое утро скажи себе одно хорошее — и верь в это. 🪞', 'Самокритика — это не мотивация, это боль. Попробуй месяц разговаривать с собой как с лучшим другом. 💛'],
    purpose: ['Смысл не находят — его создают. Запиши 3 вещи, которые делают тебя живым. Там твой ответ. 🔥', 'Ты не должен знать все ответы сейчас. Просто сделай следующий маленький шаг вперёд. 🚶'],
    physical: ['Твоё тело — твой дом. Начни с малого: один стакан воды, одна прогулка, один глубокий вдох. 🌿', 'Забота о теле — это уважение к себе. Что ты можешь сделать для своего тела сегодня? 🏃'],
  };

  const result = [];
  const weakAreas = sorted.slice(0, 2).map(([k]) => k);
  weakAreas.forEach(area => {
    const arr = advice[area];
    if (arr) result.push(arr[Math.floor(Math.random() * arr.length)]);
  });

  return result;
}
