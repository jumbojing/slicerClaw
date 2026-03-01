project(SlicerClaw)

set(MODULE_EXPORT_DIRECTIVE "")

set(SCRIPTED_SCRIPTS
  SlicerClaw.py
  )

set(SCRIPTED_RESOURCES
  Resources/Icons/SlicerClaw.png
  )

slicerMacroBuildScriptedModule(
  NAME ${PROJECT_NAME}
  SCRIPTS ${SCRIPTED_SCRIPTS}
  RESOURCES ${SCRIPTED_RESOURCES}
  WITH_GENERIC_TESTS
  )
