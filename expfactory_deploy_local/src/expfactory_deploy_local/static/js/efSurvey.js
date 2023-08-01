/*
  Convert jsonified version of experimentfactory-surveys survey.tsv into a
  jsPsych timeline using jsPsych survey plugin.
 */
function survey_convert(survey_in) {
  let num_pages = 0;
  survey_in.map(x => num_pages = Math.max(num_pages, x.page_number))
  pages = Array.from(Array(num_pages), () => Array())

  const survey_out = {
    type: jsPsychSurvey,
    pages: pages
  }

  survey_in.map(x => {
    let question_out = question_convert(x)
    pages[x.page_number - 1].push(question_out)
  })

  return [survey_out]
}

function question_convert(q_in) {
  let q_out = {}

  q_out.prompt = q_in.question_text
  q_out.required = q_in.required == "0" ? false : true

  switch(q_in.question_type) {
    case "radio":
      q_out.type = "likert"
      const option_text = q_in.option_text.split(',')
      const option_values = q_in.option_values.split(',')
      let values = option_text.map((text, index) => {
        return {"text": text, value: option_values[index]}
      })
      q_out.likert_scale_values = values
      break;
    case "checkbox":
      q_out.type = "multi-select"
      q_out.options = q_in.option_text.split(',')
      break;
    case "textfield":
      q_out.type = "text"
    case "textarea":
      break;
    case "numeric":
      q_out.type = "text"
      q_out.input_type = "number"
      break;
    case "instruction":
      q_out.type = "html"
      break;
    default:
      console.log(`${q_in.question_type} not covered by converter`)
  }
  return q_out
}
