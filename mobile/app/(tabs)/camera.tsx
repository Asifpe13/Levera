import { useRef, useState } from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { CameraView, useCameraPermissions } from 'expo-camera'

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions()
  const [facing, setFacing] = useState<'back' | 'front'>('back')
  const cameraRef = useRef<CameraView>(null)

  if (!permission) {
    return (
      <View style={styles.center}>
        <Text style={styles.text}>טוען הרשאות מצלמה...</Text>
      </View>
    )
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.text}>נדרשת הרשאת מצלמה לצילום נכסים בשטח</Text>
        <Pressable style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>אשר גישה למצלמה</Text>
        </Pressable>
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera} facing={facing} />
      <View style={styles.controls}>
        <Text style={styles.hint}>החלף בין המצלמות לפי הצורך</Text>
        <Pressable
          style={styles.flip}
          onPress={() => setFacing((f) => (f === 'back' ? 'front' : 'back'))}
        >
          <Text style={styles.buttonText}>החלף מצלמה</Text>
        </Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  camera: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, gap: 16 },
  text: { textAlign: 'center', color: '#334155', fontSize: 15, lineHeight: 22 },
  controls: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: 'rgba(0,0,0,0.55)',
    gap: 12,
  },
  hint: { color: '#e2e8f0', textAlign: 'center', fontSize: 12 },
  button: { backgroundColor: '#0d9488', padding: 14, borderRadius: 12, alignItems: 'center' },
  flip: { backgroundColor: '#334155', padding: 12, borderRadius: 12, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: '700' },
})
